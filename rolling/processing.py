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

from .arxiv import clean_for_filename


ARXIV_DIR_PDF_PROCESSED = "./arxiv_downloads_processed"


def list_processed():
    folders = []
    for folder in os.listdir(ARXIV_DIR_PDF_PROCESSED):
        dir_path = os.path.join(ARXIV_DIR_PDF_PROCESSED, folder)
        if os.path.isdir(dir_path):
            folders.append(dir_path)
    return folders


def paper_is_processed(paper_id):
    assert paper_id, "Paper ID is empty"
    paper_id = clean_for_filename(paper_id)

    for folder in list_processed():
        if os.path.basename(folder).startswith(paper_id):
            return folder
    return False


def read_processed_pdf(dir_path):
    assert os.path.exists(dir_path), f"Directory {dir_path} does not exist"
    assert os.path.isdir(dir_path), f"{dir_path} is not a directory"

    target = os.path.join(dir_path, "contents.json")
    assert os.path.exists(target), f"File {target} does not exist"

    with open(target, "r", encoding="utf-8") as f:
        contents = f.read()
    return json.loads(contents)


def process_pdf(pdf_path, callback: callable = print):
    # create output directory
    callback("Creating output directory...")
    base_name = os.path.basename(pdf_path)
    base_name = base_name.replace(".pdf", "")
    out_dir = os.path.join(ARXIV_DIR_PDF_PROCESSED, base_name)
    assert not os.path.exists(out_dir), f"Output directory {out_dir} already exists."
    os.makedirs(out_dir)
    out_dir_imgs = os.path.join(out_dir, "imgs")
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
    infer_result.draw_model(os.path.join(out_dir, f"model.pdf"))
    md_writer = FileBasedDataWriter(out_dir)
    pipe_result.dump_md(md_writer, f"paper.md", out_dir_imgs)
    pipe_result.dump_content_list(md_writer, f"contents.json", out_dir_imgs)
    callback("OK")

    callback("Extracting headers...")
    contents = read_processed_pdf(out_dir)
    headers = extract_headers(contents)
    callback("OK")

    callback("Structuring content hierarchy using AI...")
    hierarchy = structurize_content_hierarchy(headers)
    callback("OK")

    callback("Finalizing...")
    contents = fill_hierarchy(contents, headers, hierarchy)
    save_chapter_hierarchy(contents, out_dir)
    callback("OK")


def extract_headers(content):
    levels = []
    for e in content:
        if "text_level" in e:
            levels.append(e["text"])
    return levels


class Chapter(pydantic.BaseModel):
    id: int
    is_sublevel: bool


class DocHierarchy(pydantic.BaseModel):
    chapters: list[Chapter]


def structurize_content_hierarchy(
    headers: list[str],
    llm_model="gemma3:27b",
) -> DocHierarchy:

    template = """
You're given a structure of a document.
Each line has a chapter id (int) and a title (str) indicating the name of the chapter.
Your task is to consider the whole document as a tree structure and figure out which of these are main chapters (is_sublevel=False) and which are subchapters (is_sublevel=True).
For example, there might be a chapter "3. This is a title", followed by "3.1 This is some other title".
This would be indicative, that "3.1" is a subchapter of "3", therefore you would set is_sublevel=True for "3.1" and is_sublevel=False for "3".
Something else to look out for might be the appendixes, which might not have unique numbering or uses letters instead. These should still be nested if clearly possible.
Here is the outline:
""".strip()

    try:
        data = json.dumps(list(enumerate(headers)), indent=2)
        prompt = f"{template}\n{data}"
        format = DocHierarchy.model_json_schema()
        response = ollama.generate(llm_model, prompt, format=format)
        response = DocHierarchy.model_validate_json(response["response"])

        assert response is not None, "Response is None"
        assert response.chapters is not None, "Chapters is None"
        assert len(response.chapters) == len(headers), "Chapters length mismatch"
        for i, chapter in enumerate(response.chapters):
            assert chapter.id == i, f"Chapter id mismatch: {chapter.id} != {i}"

        return response
    except Exception as e:
        print(e)
        return None


@dataclass
class Chapter:
    title: str
    contents: list[dict]
    sub_chapters: list["Chapter"]


def fill_hierarchy(
    content: list,
    headers: list,
    hierarchy: DocHierarchy,
) -> list[Chapter]:
    sublevel_map = {
        h: chapter.is_sublevel for h, chapter in zip(headers, hierarchy.chapters)
    }
    results: list[Chapter] = []

    current_chapter = None
    last_parent = None

    for i, e in enumerate(content):
        if "text_level" in e:
            title = e["text"]

            if not sublevel_map[title] or current_chapter is None:
                current_chapter = Chapter(title, [], [])
                results.append(current_chapter)
                last_parent = current_chapter
                continue

            assert last_parent is not None, f"Sublevel chapter without parent? {e}"
            current_chapter = Chapter(title, [], None)
            last_parent.sub_chapters.append(current_chapter)
            continue

        if e["type"] == "text" and not e["text"].strip():
            continue
        current_chapter.contents.append(e)

    return results


def print_chapter(chapter: Chapter, level: int = 0):
    prefix = "  " * level
    print(f"{prefix}{chapter.title}")
    for k, content in enumerate(chapter.contents):
        print(f"{prefix}  > {content}")
    for j, sub in enumerate(chapter.sub_chapters or []):
        print_chapter(sub, level + 1)


def print_hierarchy(document: list[Chapter]):
    for i, chapter in enumerate(document):
        print_chapter(chapter, 0)


def save_chapter_hierarchy(chapters: list[Chapter], dir_path: str):
    filename = os.path.join(dir_path, "hierarchy.pkl")
    with open(filename, "wb") as f:
        pickle.dump(chapters, f)


def load_chapter_hierarchy(dir_path: str) -> list[Chapter]:
    filename = os.path.join(dir_path, "hierarchy.pkl")
    with open(filename, "rb") as f:
        return pickle.load(f)
