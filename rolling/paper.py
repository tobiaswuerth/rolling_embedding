import regex as re
import pickle
import numpy as np
from dataclasses import dataclass

from .pdf import clean_text

@dataclass
class Paper:
    title: str
    text: str
    embedding: list[float]
    text_segment_slices: list[tuple[int, int]]
    text_segment_embeddings: list[list[float]]

    @property
    def text_segments(self) -> list[str]:
        return [self.text[s[0] : s[1]] for s in self.text_segment_slices]
    
    def __repr__(self):
        return f'Paper({self.embedding[:5]} {self.title})'


def create_paper(
    title: str,
    text: str,
    embedding_function: callable,
    segment_lengths: list[int] = (512, 1024, 2048, 4096),
) -> Paper:

    title = clean_text(title)
    text = clean_text(text)

    max_idx = len(text)

    segment_slices = []
    for segment_length in segment_lengths:
        segment_count = max_idx // segment_length

        if segment_count < 2:
            # if the text is too short, just return the whole text as one segment and break
            segment_slices.append((0, max_idx))
            break

        actual_segment_length = max_idx / segment_count
        step_size = actual_segment_length / 2
        segment_count = segment_count + (segment_count - 1)  # assume 50% overlap

        indecies = []
        for si in range(segment_count):
            start = si * step_size
            end = min(start + actual_segment_length, max_idx)

            start = (int)(np.round(start, 0).astype(np.uint32))
            end = (int)(np.round(end, 0).astype(np.uint32))
            indecies.append((start, end))
        indecies[-1] = (indecies[-1][0], max_idx)  # assure last segment is full length

        # adjust indecies to not cut words
        for ifrom, ito in indecies:
            while ifrom > 0 and text[ifrom] != " ":
                ifrom -= 1
            if text[ifrom] == " ":
                # this is to not get pre-leading empty space
                ifrom += 1 

            while ito < max_idx and text[ito] != " ":
                ito += 1
            segment_slices.append((ifrom, ito))

    segment_slices = np.array(segment_slices, dtype=np.uint32)
    texts = [text[s[0] : s[1]] for s in segment_slices]
    segment_embeddings = embedding_function(texts)
    embedding = np.mean(segment_embeddings, axis=0)

    return Paper(
        title=title,
        text=text,
        embedding=embedding,
        text_segment_slices=segment_slices,
        text_segment_embeddings=segment_embeddings,
    )


def print_paper(paper: Paper):
    print(f"Paper: {paper.embedding[:5]} {paper.title}")
    for i, (s, e) in enumerate(paper.text_segment_slices):
        print(f" > {i:03d} {paper.text_segment_embeddings[i][:5]} {paper.text[s:e]}")


def save_paper(paper: Paper, path: str):
    with open(path, "wb") as f:
        pickle.dump(paper, f)


def load_paper(path: str) -> Paper:
    with open(path, "rb") as f:
        paper = pickle.load(f)
    return paper
