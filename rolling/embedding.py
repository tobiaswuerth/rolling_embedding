import ollama
import numpy as np
from scipy.spatial.distance import cosine


def get_embedding(text):
    emb = ollama.embeddings(model="mxbai-embed-large", prompt=text)
    return np.array(emb.embedding, dtype=np.float64)


def get_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)


def create_corpus_from_text(file, n=512):
    text = ""
    with open(file, "r", encoding="UTF-8") as f:
        text += f.read()

    return Corpus(text, n)


class Corpus:
    def __init__(self, text, n=512):
        self.text = text

        self.parts = [text[i : i + n] for i in range(0, len(text), n)]
        self.embeddings = [get_embedding(part) for part in self.parts]
