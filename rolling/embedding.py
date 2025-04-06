import ollama
import numpy as np
from scipy.spatial.distance import cosine


def get_embedding(text):
    emb = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return np.array(emb.embedding, dtype=np.float64)


def get_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)
