import os

from pypdf import PdfReader
from streamlit.runtime.uploaded_file_manager import UploadedFile


def get_file_extension(file):
    if isinstance(file, UploadedFile):
        filename = file.name
    else:
        filename = file.filename
    _, extension = os.path.splitext(filename)
    return extension.lower().lstrip('.')


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text
