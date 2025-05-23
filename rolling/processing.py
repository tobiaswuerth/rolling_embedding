import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
import json
from json import JSONEncoder
import pydantic
import ollama
from dataclasses import dataclass
import pickle
import random

from .arxiv import clean_for_filename, pdf_is_downloaded


ARXIV_DIR_PDF_PROCESSED = "./arxiv_downloads_processed"
DOC_STRUCTURIZED_FILENAME = "doc_structurized.pkl"
DOC_MARKDOWN_FILENAME = "paper.md"


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
    if not os.path.exists(struct_path):
        return False
    return proc_dir


def delete_pdf_structurized(paper_id):
    assert paper_id, "Paper ID is empty"
    assert pdf_is_structurized(paper_id), f"Paper {paper_id} is not structurized"
    proc_dir = pdf_is_processed(paper_id)
    assert proc_dir, f"Paper {paper_id} is not processed"
    struct_path = os.path.join(proc_dir, DOC_STRUCTURIZED_FILENAME)
    assert os.path.exists(struct_path), f"File {struct_path} does not exist"
    os.remove(struct_path)


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
    infer_result.draw_model(os.path.join(proc_dir, "model.pdf"))
    md_writer = FileBasedDataWriter(proc_dir)
    pipe_result.dump_md(md_writer, DOC_MARKDOWN_FILENAME, out_dir_imgs)
    pipe_result.dump_content_list(md_writer, "contents.json", out_dir_imgs)
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
    llm_model="mistral-small3.1",
) -> DocHierarchy__:

    template = """
You are an expert in document structure and hierarchy.
You are given a list of chapter titles from a document.
Each title is provided as a tuple `(id, title)`, where `id` is a unique integer (its original position/enumeration in the document) and `title` is the string content of the header.
Your task is to determine the hierarchical level (`level`) for each chapter based on its title and its position relative to other titles in the list. The `level` is an integer representing the depth in the document structure (e.g., 0 for top-level chapters, 1 for subchapters, 2 for sub-subchapters, etc.).

### Strict Hierarchy Rules:
Apply these rules rigorously to determine the level of each chapter:

1.  **Top-Level Chapters (Level 0):**
    -   Chapters with primary sequential numbering (e.g., "1. Title", "2. Another Title", "3. Section", etc.). This also includes alphabetical primary numbering (e.g., "A. Section", "B. Section").
    -   Standard front matter, back matter, or major sections without numbering (e.g., "Title Page", "Copyright", "Dedication", "Acknowledgements", "Contents", "Abstract", "Preface", "Introduction", "Conclusion", "Appendix", "References", "Index"). These sections are also level 0.

2.  **Subchapters (Level 1 and beyond):**
    -   Chapters with nested numbering (e.g., "1.1 Subtitle", "1.2 Another Subtitle", "2.1 Subsection", "A.1 Subsection").
    -   The level of a numbered subchapter is determined by the count of numeric or alphanumeric components separated by periods (dots) in its prefix, relative to the most recent preceding parent chapter.
    -   For example, if "1." is level 0, then "1.1", "1.2", "1.3" are level 1. If "1.2" is level 1, then "1.2.1", "1.2.2" are level 2.

3.  **Handling Transitions and Non-Numbered Sections:**
    -   **Crucially:** A numbered chapter (like "1. Title", "2. Title", etc.) that follows one or more non-numbered level 0 sections (such as "Abstract" or "Introduction") should **always** be treated as a new level 0 chapter. It starts the main numbered sequence of the document and should **never** be nested under the preceding non-numbered section.
    -   Chapters without clear numbering (and not in the list of standard level 0 sections) should have their level inferred from the *immediately preceding chapter*. If the preceding chapter is level N, the current non-numbered chapter is likely level N or N+1 if its content suggests it's a subdivision. However, prioritize the rules for numbered sections.

### Guidelines:
-   Maintain the original `id` for each chapter in the output.
-   The output list must contain the exact same number of chapters as the input list.
-   Assign a non-negative integer `level` (0 or greater) to each chapter.
-   Pay close attention to the numbering patterns as the primary indicator of hierarchy as well as their semantical belonging considering the table of contents as a whole.

Your input is:
"""

    try:
        data = json.dumps(list(enumerate(headers)))
        prompt = f"{template}\n{data}"
        context_length = max(4096, len(prompt.split()) * 3)
        seed = random.randint(0, 2**30 - 1)
        print(f"Context length: {context_length} / Seed: {seed}")
        format = DocHierarchy__.model_json_schema()
        response = ollama.generate(
            llm_model,
            prompt,
            format=format,
            options={
                "num_ctx": context_length,
                "seed": seed,
            },
        )
        response = DocHierarchy__.model_validate_json(response["response"])

        assert response is not None, "Response is None"
        assert response.chapters is not None, "Chapters is None"
        assert len(response.chapters) == len(headers), "Chapters length mismatch"
        for i, chapter in enumerate(response.chapters):
            assert chapter.id == i, f"Chapter id mismatch: {chapter.id} != {i}"
            assert chapter.level >= 0, "Chapter level is negative"

        return response
    except Exception as e:
        print(e)
        return None


@dataclass
class Content:
    type: str
    level: int
    data: dict
    children: list["Content"]


class ContentJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Content):
            data = obj.data.copy()
            data.pop("type", None)  # already present on content obj
            data.pop("page_idx", None)
            data.pop("text_level", None)

            for key in [
                "img_caption",
                "img_footnote",
                "table_caption",
                "table_footnote",
            ]:
                if key in data and not data[key]:
                    data.pop(key, None)

            result = {
                "type": obj.type,
                "level": obj.level,
                "data": data,
            }
            if obj.type in ("chapter", "document"):
                result["children"] = [self.default(child) for child in obj.children]

            return result
        return super().default(obj)


def build_document(content: list, headers: list, hierarchy: DocHierarchy__) -> Content:
    sublevel_map = {h: chapter.level for h, chapter in zip(headers, hierarchy.chapters)}
    document = Content(type="document", data={}, children=[], level=-1)
    parents_stack: list[Content] = []

    def find_unique_name(name: str, nodes: list[Content]) -> str:
        existing_names = {child.data["text"].lower() for child in nodes if "text" in child.data}
        if name.lower() not in existing_names:
            return name

        suffix = 2
        while f"{name} ({suffix})".lower() in existing_names:
            suffix += 1
            if suffix > 1000:
                raise ValueError(f"Too many duplicates for {name}")
        return f"{name} ({suffix})"

    for e in content:
        if e["type"] == "text" and not e["text"].strip():
            continue

        # handle chapters
        if "text_level" in e:
            level = sublevel_map[e["text"]]

            while parents_stack and level <= parents_stack[-1].level:
                parents_stack.pop()

            target_list = document.children if not parents_stack else parents_stack[-1].children
            name = find_unique_name(e["text"], target_list)
            e["text"] = name
            node = Content(type="chapter", data=e, children=[], level=level)
            target_list.append(node)
            parents_stack.append(node)
            continue

        # handle all other types
        if not parents_stack:
            # create empty chapter for entrys without parent
            node = Content(type="chapter", data={"text": "<?>"}, children=[], level=0)
            document.children.append(node)
            parents_stack.append(node)

        level = parents_stack[-1].level + 1
        node = Content(type=e["type"], data=e, children=[], level=level)
        parents_stack[-1].children.append(node)

    return document


def save_document(document: Content, dir_path: str):
    filename = os.path.join(dir_path, DOC_STRUCTURIZED_FILENAME)
    with open(filename, "wb") as f:
        pickle.dump(document, f)


def load_document(dir_path: str) -> Content:
    filename = os.path.join(dir_path, DOC_STRUCTURIZED_FILENAME)
    with open(filename, "rb") as f:
        return pickle.load(f)


def load_markdown(dir_path: str) -> Content:
    filename = os.path.join(dir_path, DOC_MARKDOWN_FILENAME)
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def printable_content(contents:Content|list[Content], indent=2) -> str:
    return json.dumps(contents, cls=ContentJSONEncoder, indent=indent)


def get_content_hierarchy(content: Content) -> list[dict]:
    if content.type == "document":
        return [
            get_content_hierarchy(child)
            for child in content.children
            if child.type == "chapter"
        ]

    result = {
        content.data["text"]: [
            get_content_hierarchy(child) for child in content.children
            if child.type == "chapter"
        ]
    }
    return result


class ChapterSummary(pydantic.BaseModel):
    chapter_title: str
    summaries: list[str]

def summarize_chapter(chapter: Content, llm_model="gemma3:12b", min_tokens=4096):
    prompt = f"""
**Role:** Expert Knowledge Distiller.

**Objective:** Analyze the 'Current Chapter Content'. Your **sole focus** is to extract and synthesize the **absolute core knowledge** (key findings, critical methods/definitions, essential results, crucial context) presented within. Disregard chapter structure and meta-commentary. The goal is a highly condensed summary enabling understanding of the chapter's *contribution* without reading it.

**CRITICAL Instructions:**
1.  **NO OUTLINES / STRUCTURE:** **Do NOT** list section titles, subsection numbers, or describe the chapter's organization (e.g., AVOID "This chapter discusses X in section Y"). Summarize the *information itself*, not the chapter's structure.
2.  **SUBSTANCE ONLY:** Generate summary points **only** if the chapter presents significant *new substantive information* (e.g., a new technique, a key result, a core definition) compared to previous summaries. Ignore introductory phrases, forward references, or purely structural sections.
3.  **EXTREME CONCISENESS:** Aim for **highly condensed** points (like bullet points). Capture the *essence* only. If a detail isn't critical for understanding the main point, omit it. Think "executive summary" level for each key concept.
4.  **Accuracy:** Base summaries strictly on the provided 'Current Chapter Content'. No external knowledge or interpretation.
5.  **Empty if Necessary:** If a chapter contains primarily structure, table of contents, people, introductions, references, or information already covered, return an empty `summaries` list (`[]`). Do not summarize just for the sake of summarizing.
6.  **Output Format:**
    * Return `[]` for `summaries` if no new *substantive* core knowledge is found.
    * Otherwise, return a list of concise strings in `summaries`.
    * The `chapter_title` field *must* exactly match the 'Current Chapter Title'.

**Context:**
* Current Chapter Title: ``{chapter.data['text']}`` (Use this exact title in output)

**Current Chapter Content to Distill:**
```{printable_content(chapter, indent=None)}```

Generate the JSON output conforming to the ChapterSummary structure.
"""

    try:
        word_count = len(prompt.split())
        context_length = max(min_tokens, word_count * 3)
        seed = random.randint(0, 2**30 - 1)
        print(f"Word-Count: {word_count} / Context length: {context_length} / Seed: {seed}")
        format = ChapterSummary.model_json_schema()
        response = ollama.generate(
            llm_model,
            prompt,
            format=format,
            options={
                "num_ctx": context_length,
                "seed": seed,
            },
        )

        response = ChapterSummary.model_validate_json(response["response"])
        assert response is not None, "Response is None"
        assert response.chapter_title.lower().strip() == chapter.data["text"].lower().strip(), "Chapter title mismatch"

        return response
    except Exception as e:
        print(e)
        return None