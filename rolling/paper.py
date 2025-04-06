import regex as re
import pickle
# import nltk
# from nltk.tokenize import sent_tokenize
from dataclasses import dataclass

from .embedding import get_embedding


@dataclass
class Paper:
    title: str
    text: str
    nodes: list['PaperNode']

    @property
    def embeddings(self) -> list[float]:
        def _get_embeddings(node: PaperNode) -> list[float]:
            embs = [node.embedding]
            if node.children:
                for child in node.children:
                    embs.extend(_get_embeddings(child))
            return embs

        embs = []
        for node in self.nodes:
            embs.extend(_get_embeddings(node))
        return embs
    
    @property
    def texts(self) -> str:
        def _get_texts(node: PaperNode) -> str:
            texts = [node.text]
            if node.children:
                for child in node.children:
                    texts.extend(_get_texts(child))
            return texts

        txts = []
        for node in self.nodes:
            txts.extend(_get_texts(node))
        return txts
    

@dataclass
class PaperNode:
    text: str
    embedding: list[float]
    children: list['PaperNode'] = None

    
def create_paper(title:str, text:str, min_sentence_length=256, max_sentence_length=2048) -> Paper:
    title = re.sub(r'\s+', ' ', title).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    # nltk.download('punkt', quiet=True, raise_on_error=True)
    # nltk.download('punkt_tab', quiet=True, raise_on_error=True)
    # sentences = sent_tokenize(text)
    sentences = text.split(' ')

    # combine short sentences
    valid_sentences = []
    current_sentence = ''
    for sentence in sentences:
        current_sentence += ' ' + sentence.strip()
        if len(current_sentence.strip()) >= min_sentence_length:
            valid_sentences.append(current_sentence.strip())
            current_sentence = ''
    if current_sentence:
        valid_sentences[-1] += ' ' + current_sentence.strip()
    
    # generate base nodes
    all_nodes = []
    for sent in valid_sentences:
        emb = get_embedding(sent)
        all_nodes.append(PaperNode(text=sent, embedding=emb))

    # generate tree layer
    layer_groups = []
    current_group = []
    for node in all_nodes:
        group_txt_length = sum(len(n.text) for n in current_group)

        if group_txt_length + len(node.text) > max_sentence_length:
            if len(current_group) > 0:
                layer_groups.append(current_group)
            current_group = [node]
            continue
        
        current_group.append(node)
    
    if len(current_group) > 0:
        layer_groups.append(current_group)

    root_nodes = []
    for group in layer_groups:
        if len(group) == 1:
            root_nodes.append(group[0])
            continue

        group_text = ' '.join([node.text for node in group])
        group_emb = get_embedding(group_text)
        root_node = PaperNode(text=group_text, embedding=group_emb, children=group)
        root_nodes.append(root_node)
    
    assert len(root_nodes) > 0, 'No root nodes found.'
    return Paper(title, text, root_nodes)


def print_paper(paper: Paper, indent: int = 2):
    print(f'Paper: {paper.title}')

    def print_node(node: PaperNode, level: int = 0):
        print(' ' * indent * level + f'> {node.embedding[:3]} {node.text}')
        if node.children:
            for child in node.children:
                print_node(child, level + 1)

    for node in paper.nodes:
        print_node(node, 1)


def save_paper(paper: Paper, path: str):
    with open(path, 'wb') as f:
        pickle.dump(paper, f)


def load_paper(path: str) -> Paper:
    with open(path, 'rb') as f:
        paper = pickle.load(f)
    return paper
