import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import json
import pydantic
import ollama
from dataclasses import dataclass
import pickle

from .arxiv import clean_for_filename, pdf_is_downloaded


ARXIV_DIR_PDF_PROCESSED = "./arxiv_downloads_processed"
DOC_STRUCTURIZED_FILENAME = "doc_structurized.pkl"


def list_processed():
    folders = []
    for folder in os.listdir(ARXIV_DIR_PDF_PROCESSED):
        dir_path = os.path.join(ARXIV_DIR_PDF_PROCESSED, folder)
        if os.path.isdir(dir_path):
            folders.append(dir_path)
    return folders


def pdf_is_processed(paper_id):
    assert paper_id, "Paper ID is empty"
    paper_id = clean_for_filename(paper_id)

    for folder in list_processed():
        if os.path.basename(folder).startswith(paper_id):
            return folder
    return False


def pdf_is_structurized(paper_id):
    assert paper_id, "Paper ID is empty"
    proc_dir = pdf_is_processed(paper_id)
    if not proc_dir:
        return False
    struct_path = os.path.join(proc_dir, DOC_STRUCTURIZED_FILENAME)
    return os.path.exists(struct_path)


def read_processed_contentsJSON(dir_path):
    assert os.path.exists(dir_path), f"Directory {dir_path} does not exist"
    assert os.path.isdir(dir_path), f"{dir_path} is not a directory"

    target = os.path.join(dir_path, "contents.json")
    assert os.path.exists(target), f"File {target} does not exist"

    with open(target, "r", encoding="utf-8") as f:
        contents = f.read()
    return json.loads(contents)


def process_pdf(paper_id, callback: callable = print):
    assert paper_id, "Paper ID is empty"
    pdf_path = pdf_is_downloaded(paper_id)
    assert pdf_path, f"PDF for paper {paper_id} is not downloaded"

    # create output directory
    callback("Creating output directory...")
    base_name = os.path.basename(pdf_path)
    base_name = base_name.replace(".pdf", "")
    proc_dir = os.path.join(ARXIV_DIR_PDF_PROCESSED, base_name)
    assert not os.path.exists(proc_dir), f"Output directory {proc_dir} already exists."
    os.makedirs(proc_dir)
    out_dir_imgs = os.path.join(proc_dir, "imgs")
    os.makedirs(out_dir_imgs)
    callback("OK")

    # read PDF
    callback("Reading PDF...")
    pdf_bytes = FileBasedDataReader("").read(pdf_path)
    doc = PymuDocDataset(pdf_bytes)
    callback("OK")

    # process PDF
    callback("Processing PDF using AI...")
    image_writer = FileBasedDataWriter(out_dir_imgs)
    is_ocr = doc.classify() == SupportedPdfParseMethod.OCR
    infer_result = doc.apply(doc_analyze, ocr=is_ocr)
    pipe_result = (
        infer_result.pipe_ocr_mode(image_writer)
        if is_ocr
        else infer_result.pipe_txt_mode(image_writer)
    )
    callback("OK")

    # dump results
    callback("Dumping results...")
    infer_result.draw_model(os.path.join(proc_dir, f"model.pdf"))
    md_writer = FileBasedDataWriter(proc_dir)
    pipe_result.dump_md(md_writer, f"paper.md", out_dir_imgs)
    pipe_result.dump_content_list(md_writer, f"contents.json", out_dir_imgs)
    # pipe_result.dump_middle_json(md_writer, f'middle.json')
    callback("OK")


def structurize_pdf(paper_id, callback: callable = print):
    assert paper_id, "Paper ID is empty"

    callback('Loading contents...')
    proc_dir = pdf_is_processed(paper_id)
    assert proc_dir, f"Paper {paper_id} is not processed"
    contents = read_processed_contentsJSON(proc_dir)
    callback("OK")

    callback("Extracting headers...")
    headers = extract_headers(contents)
    callback("OK")

    callback("Hierarchizing headers using AI...")
    hierarchy = hierarchize_headers(headers)
    callback("OK")

    callback("Finalizing...")
    doc = build_document(contents, headers, hierarchy)
    save_document(doc, proc_dir)
    callback("OK")


def extract_headers(content):
    levels = []
    for e in content:
        if "text_level" in e:
            levels.append(e["text"])
    return levels


class Chapter__(pydantic.BaseModel):
    id: int
    level: int

class DocHierarchy__(pydantic.BaseModel):
    chapters: list['Chapter__']


def hierarchize_headers(
    headers: list[str],
    llm_model="gemma3:12b",
) -> DocHierarchy__:

    template = """
You're given a structure of a document.
Each line has a chapter id (int) and a title (str) indicating the name of the chapter.
Your task is to consider the whole document as a tree structure and figure out which of these chapters belong onto which level.
For example, there might be a chapter "3. This is a title", followed by "3.1 This is some other title".
This would be indicative, that "3.1" is a subchapter of "3", therefore you would set level=1 "3.1" and level=0 for "3".
It's also possible that the naming scheme is different, for example "A. This is a title", followed by "A.1 This is some other title".
This would be indicative, that "A.1" is a subchapter of "A", therefore you would set level=1 for "A.1" and level=0 for "A".
If you encounter further nesting, feel free to increase the level by 1 for each subchapter.
Typically though, any main chapter will be at level 0, any subchapter at level 1, and any sub-subchapter at level 2 etc.
This would be indicative, that "A.1.1" is a subchapter of "A.1", therefore you would set level=2 for "A.1.1" and level=1 for "A.1" etc.
Also note, not all naming conventions follow a clear logic.
Given the document structure as a whole, there might be sections where it is implicitly clear that a chapter is a subchapter of another chapter, even if the naming scheme does not follow a clear logic.
For example the appendixes, which might not have unique numbering or uses letters instead.
If for some reason you encounter a title which is clearly a mistake, please set the level to -1, although that should not happen often.
You must include the exact same amount of chapters as given, any missing ones will be considered a mistake.
Here is the outline:
""".strip()

    try:
        data = json.dumps(list(enumerate(headers)))
        prompt = f"{template}\n{data}"
        format = DocHierarchy__.model_json_schema()
        response = ollama.generate(llm_model, prompt, format=format)
        response = DocHierarchy__.model_validate_json(response["response"])

        assert response is not None, "Response is None"
        assert response.chapters is not None, "Chapters is None"
        assert len(response.chapters) == len(headers), "Chapters length mismatch"
        for i, chapter in enumerate(response.chapters):
            assert chapter.id == i, f"Chapter id mismatch: {chapter.id} != {i}"
            assert chapter.level >= -1, f"Chapter level mismatch: {chapter.level} < -1"

        return response
    except Exception as e:
        print(e)
        return None


@dataclass
class Content:
    type: str
    data: dict
    children: list["Content"]
    level: int


def build_document(content: list, headers: list, hierarchy: DocHierarchy__) -> Content:
    sublevel_map = {h: chapter.level for h, chapter in zip(headers, hierarchy.chapters)}
    document = Content(type="document", data={}, children=[], level=-1)
    parents_stack: list[Content] = []

    for e in content:
        if e["type"] == "text" and not e["text"].strip():
            continue

        # handle chapters
        if "text_level" in e:
            level = sublevel_map[e["text"]]
            node = Content(type="chapter", data=e, children=[], level=level)

            if not parents_stack:
                document.children.append(node)
                parents_stack.append(node)
                continue

            while parents_stack and level <= parents_stack[-1].level:
                parents_stack.pop()
            
            (parents_stack[-1].children if parents_stack else document.children).append(node)
            parents_stack.append(node)
            continue

        # handle all other types
        if not parents_stack:
            # create empty chapter for entrys without parent
            node = Content(type="chapter", data={'text': '<?>'}, children=[], level=0)
            document.children.append(node)
            parents_stack.append(node)
        
        level = parents_stack[-1].level + 1
        node = Content(type=e["type"], data=e, children=[], level=level)
        parents_stack[-1].children.append(node)

    return document


def print_content(contents:Content|list[Content], level:int=0):
    if isinstance(contents, Content):
        contents = [contents]

    prefix = "--" * level
    for content in contents:
        print(f"{prefix} [{content.level}] {content.type} {content.data}")
        if content.children:
            print_content(content.children, level + 1)


def save_document(document: Content, dir_path: str):
    filename = os.path.join(dir_path, DOC_STRUCTURIZED_FILENAME)
    with open(filename, "wb") as f:
        pickle.dump(document, f)


def load_document(dir_path: str) -> Content:
    filename = os.path.join(dir_path, DOC_STRUCTURIZED_FILENAME)
    with open(filename, "rb") as f:
        return pickle.load(f)
