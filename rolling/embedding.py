import torch
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    XLMRobertaTokenizerFast,
)
from scipy.spatial.distance import cosine
import math
from tqdm import tqdm
import numpy as np


def get_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)


class GTEEmbeddingModel(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = "Alibaba-NLP/gte-multilingual-base"
        self.tokenizer: XLMRobertaTokenizerFast = AutoTokenizer.from_pretrained(model_name)
        self.model: torch.nn.Module = AutoModelForTokenClassification.from_pretrained(model_name, trust_remote_code=True, torch_dtype=torch.float16)
        self.model.to(self.device).eval()

        self.max_size = self.model.config.max_position_embeddings

    def encode(self, texts: list[str], batch_size: int = 32, progressbar=False):
        if isinstance(texts, str):
            texts = [texts]

        num_texts = len(texts)
        iter = range(0, num_texts, batch_size)
        if progressbar:
            iter = tqdm(iter, total=math.ceil(num_texts / batch_size))

        embeddings = []
        for i in iter:
            batch = texts[i : i + batch_size]
            embeddings.append(self._encode(batch))

        return np.vstack(embeddings)

    @torch.no_grad()
    def _encode(self, texts: list[str]):
        tokens = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=self.max_size,
        )

        model_out = self.model(
            input_ids=tokens.input_ids.to(self.device),
            attention_mask=tokens.attention_mask.to(self.device),
            return_dict=True,
        )

        emb = model_out.last_hidden_state[:, 0]
        emb = torch.nn.functional.normalize(emb, dim=-1)
        emb = emb.cpu().numpy()
        return emb
