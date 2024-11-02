from collections import defaultdict

import streamlit as st

from config.configuration import configs
from services import hana_service as hs
from services import openai_service as ois
from services import sap_ai_service as sas
from services.decorators import timing


def get_active_ai_service():
    service = None
    if configs['sapAI.active']:
        service = sas
    elif configs['openai.active']:
        service = ois
    return service


def get_embeddings():
    service = get_active_ai_service()
    return service.get_embeddings() if service else None


def get_llm():
    service = get_active_ai_service()
    return service.get_llm() if service else None


@timing(print_args=True)
def vectorize_text(text):
    return get_embeddings().embed_query(text)


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_relevant_context'])
def get_relevant_context(query):
    query_embedding = vectorize_text(query)
    chunks_rows = hs.retrieve_relevant_chunks(query_embedding)
    section_priorities = {section['section']: section['priority'] for section in
                          configs['hana.embedding.contextSections']}
    max_chars = int(configs['sapAI.openai.maxTokens'] * 2.5)
    sorted_chunks = sorted(
        [(document_id, url, section, text, section_priorities.get(section))
         for document_id, url, section, text in chunks_rows],
        key=lambda x: x[4]
    )
    selected_chunks = []
    current_length = 0
    for document_id, url, section, text, _ in sorted_chunks:
        if current_length + len(text) <= max_chars:
            selected_chunks.append((document_id, url, section, text))
            current_length += len(text)
        else:
            break
    merged_chunks = defaultdict(str)
    for document_id, url, section, text in selected_chunks:
        key = (document_id, url, section)
        merged_chunks[key] += text + ' '
    formatted_context = [
        {
            "document": {
              "url": url,
              "id": document_id
            },
            "section": section,
            "text": text.strip()
        }
        for (document_id, url, section), text in merged_chunks.items()
    ]
    # context = "\n\n".join([f"Document ID: {chunk[0]}, Section: {chunk[1]}\n{chunk[2]}" for chunk in chunks])
    return formatted_context
