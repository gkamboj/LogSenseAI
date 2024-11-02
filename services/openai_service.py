import os

import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config.configuration import configs


def get_llm():
    os.environ['OPENAI_API_KEY'] = configs['openai.key']
    os.environ['OPENAI_MODEL'] = configs['openai.model']
    # return ChatOpenAI(model_name=configs['openai.model'], openai_api_key=configs['openai.key'])
    return ChatOpenAI(temperature=configs['openai.temperature'])


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_embeddings'])
def get_embeddings():
    return OpenAIEmbeddings()