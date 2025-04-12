from pypdf import PdfReader
import os
import re


def list_pdfs(directory="./arxiv_downloads"):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            files.append(os.path.join(directory, file))
    return files


def list_pdfs_processed(directory="./arxiv_downloads_processed"):
    files = []
    for file in os.listdir(directory):
        if file.endswith(".pkl"):
            files.append(os.path.join(directory, file))
    return files


def read_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        text += page.extract_text()

    return clean_text(text)


def clean_text(txt):
    return re.sub(r"\s+", " ", txt).strip()
