import pymupdf
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
    doc = pymupdf.open(file_path)

    text = "\n".join([
        page.get_text()
        for page in doc
    ])

    return clean_text(text)


def clean_text(txt):
    return re.sub(r"\s+", " ", txt).strip()


def chunk_text(text, size=256, hard_cut=False, overlap=True):
    text_length = len(text)
    if text_length <= size:
        return [text]
    if size <= 1:
        return text.split(' ')

    step = size // 2 if overlap else size
    chunks = []
    txt_from = 0
    while txt_from < text_length:
        if not hard_cut and text[txt_from] != " ":
            # check if there is a spacing nearby, else hardcut
            lookbefore = max(0, txt_from - step + 1)
            if " " in text[lookbefore:txt_from]:
                while txt_from > 0 and text[txt_from] != " ":
                    txt_from -= 1
        if text[txt_from] == " ":
            txt_from += 1

        txt_to = min(text_length, txt_from + size)
        if not hard_cut and txt_to < text_length and text[txt_to] != " ":
            # check if there is a spacing nearby, else hardcut
            lookahead = min(text_length, txt_to + step - 1)
            if " " in text[txt_from:lookahead]:
                while txt_to < text_length and text[txt_to] != " ":
                    txt_to += 1
        chunks.append(text[txt_from:txt_to])
        txt_from += step
    return chunks
