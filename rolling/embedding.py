import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
from scipy.spatial.distance import cosine


def get_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)


class GTEEmbeddingModel(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = "Alibaba-NLP/gte-multilingual-base"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model: torch.nn.Module = AutoModelForTokenClassification.from_pretrained(
            model_name, trust_remote_code=True, torch_dtype=torch.float16
        )
        self.model.to(self.device).eval()

        self.vocab_size = self.model.config.vocab_size
        self.max_size = self.model.config.max_position_embeddings

    @torch.no_grad()
    def encode(self, texts: list[str], batch_size: int = 64):
        if isinstance(texts, str):
            texts = [texts]

        num_texts = len(texts)
        embeddings = []
        for n, i in enumerate(range(0, num_texts, batch_size)):
            batch = texts[i : i + batch_size]
            embeddings.append(self._encode(batch))

        embeddings = torch.cat(embeddings, dim=0)
        embeddings = embeddings.cpu().numpy()
        return embeddings

    @torch.no_grad()
    def _encode(self, texts: list[str]):
        text_input = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=self.max_size,
        )
        text_input = {k: v.to(self.device) for k, v in text_input.items()}
        model_out = self.model(**text_input, return_dict=True)

        dense_vecs = model_out.last_hidden_state[:, 0]
        dense_vecs = torch.nn.functional.normalize(dense_vecs, dim=-1)
        return dense_vecs
