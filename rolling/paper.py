import regex as re
import pickle
import nltk
from nltk.tokenize import sent_tokenize
from dataclasses import dataclass

from .embedding import get_embedding


@dataclass
class Paper:
    title: str
    root: 'PaperNode'


@dataclass
class PaperNode:
    text: str
    embedding: list[float]
    children: list['PaperNode'] = None

    
def create_paper(title:str, text:str, min_sentence_length=8, concat_factor=4) -> Paper:
    nltk.download('punkt', quiet=True, raise_on_error=True)
    nltk.download('punkt_tab', quiet=True, raise_on_error=True)

    # clean and split text
    title = re.sub(r'\s+', ' ', title).strip()
    text = re.sub(r'\s+', ' ', text).strip()

    sentences = sent_tokenize(text)

    # combine short sentences
    valid_sentences = []
    current_sentence = ''
    for sentence in sentences:
        if len(sentence) < min_sentence_length:
            current_sentence += sentence + ' '
            continue

        valid_sentences.append(current_sentence + sentence)
        current_sentence = ''

    # generate base nodes
    all_nodes = []
    for sent in valid_sentences:
        emb = get_embedding(sent)
        all_nodes.append(PaperNode(text=sent, embedding=emb))

    # combine multiple nodes to create hierarchical structure
    def combine_nodes(nodes):
        assert len(nodes) > 1, "Cannot combine a single node"

        splits = []
        for i in range(0, len(nodes), concat_factor):
            parts = nodes[i:i + concat_factor]
            if len(parts) == 1:
                splits[-1].append(parts[0])
                continue

            splits.append(parts)

        combined_nodes = []
        for parts in splits:
            combined_text = ' '.join([node.text for node in parts])
            combined_emb = get_embedding(combined_text)
            combined_node = PaperNode(text=combined_text, embedding=combined_emb, children=parts)
            combined_nodes.append(combined_node)

        return combined_nodes

    combined_nodes = all_nodes
    while len(combined_nodes) > 1:
        combined_nodes = combine_nodes(combined_nodes)
        all_nodes += combined_nodes

    assert len(combined_nodes) == 1, "Failed to combine nodes into a single node"
    root = combined_nodes[0]
    
    paper = Paper(title=title, root=root)
    return paper


def print_paper(paper: Paper, indent: int = 2):
    print(f'Paper: {paper.title}')

    def print_node(node: PaperNode, level: int = 0):
        print(' ' * indent * level + f'> {node.embedding[:3]} {node.text}')
        if node.children:
            for child in node.children:
                print_node(child, level + 1)

    print_node(paper.root)


def save_paper(paper: Paper, path: str):
    with open(path, 'wb') as f:
        pickle.dump(paper, f)


def load_paper(path: str) -> Paper:
    with open(path, 'rb') as f:
        paper = pickle.load(f)
    return paper
