import concurrent
import os
import re
from contextlib import closing

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.configuration import configs
from services import common_service as cs
from services import file_service as fs
from services import hana_service as hs
from services.decorators import timing

SCHEMA = configs['hana.schema']
BASE_PATH = '' # Enter path of base folder containing KBAs folder
KBA_DIRECTORY = BASE_PATH + '/KBAs'


def identify_kba_sections(text):
    sections = []
    current_section = 'Header'
    section_pattern = r'^(Attributes|Cause|Environment|Keywords|Other Terms|Products|Reason and Prerequisites|Reproducing the Issue|Resolution|See Also|References|This document refers to|Symptom)$'
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(section_pattern, line):
            current_section = line
        sections.append((line, current_section))
    return sections


def split_document_into_chunks_with_metadata(document_text):
    sections = identify_kba_sections(document_text)
    chunks_with_metadata = []
    current_chunk = sections[0][0]
    current_section = sections[0][1]
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '. ', ' ', ''],
        chunk_size=400,
        chunk_overlap=50,
        length_function=len
    )
    for line, section in sections[1:]:
        if section != current_section:
            chunks = splitter.split_text(current_chunk)
            for chunk in chunks:
                chunks_with_metadata.append({
                    'text': chunk,
                    'metadata': {
                        'section': current_section
                    }
                })
            current_chunk = line
            current_section = section
        else:
            current_chunk += line + '\n'
    chunks_with_metadata.append({
        'text': ''.join(current_chunk),
        'metadata': {
            'section': current_section
        }
    })
    return chunks_with_metadata


def generate_embeddings(chunks_with_metadata):
    embeddings_model = cs.get_embeddings()
    for chunk in chunks_with_metadata:
        embedding = embeddings_model.embed_query(chunk['text'])
        chunk['embedding'] = embedding
    return chunks_with_metadata


def store_embeddings_in_hana(doc_id, chunks_with_metadata):
    with closing(hs.get_hana_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            for i, chunk in enumerate(chunks_with_metadata, start=1):
                padded_number = f"{i:03d}"
                chunk_id = f'{doc_id}_{padded_number}'
                cursor.execute(
                    f'INSERT INTO {SCHEMA}.Embeddings (Chunk_Id, Document_Id, Text, Embedding, Section) VALUES (?, ?, ?, ?, ?)',
                    (chunk_id, doc_id, chunk['text'], chunk['embedding'], chunk['metadata']['section'].lower())
                )
            conn.commit()


@timing(print_args=True)
def insert_document_embeddings(pdf_path, doc_id):
    document_text = fs.extract_text_from_pdf(pdf_path)
    chunks_with_metadata = split_document_into_chunks_with_metadata(document_text)
    chunks_with_embeddings = generate_embeddings(chunks_with_metadata)
    store_embeddings_in_hana(doc_id, chunks_with_embeddings)


def insert_kbas_embeddings(max_workers=5):
    prcoessed_files_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'embeddings_processed_files.txt')
    with open(prcoessed_files_file, 'r') as file:
        processed_files = file.read().splitlines()

    def process_file(filename):
        try:
            if filename not in processed_files:
                insert_document_embeddings(os.path.join(KBA_DIRECTORY, filename), filename.split('.')[0])
                print(f'Saved embeddings for {filename}')
                with open(prcoessed_files_file, 'a') as file:
                    file.write(filename + '\n')
        except Exception as e:
            print(f'Error processing {filename}: {e}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, filename) for filename in os.listdir(KBA_DIRECTORY)]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'An error occurred: {e}')


insert_kbas_embeddings()
