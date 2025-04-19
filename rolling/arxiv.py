import re
import os
import arxiv

arxiv_download_dir = "./arxiv_downloads"
arxiv_processed_dir = "./arxiv_downloads_processed"


def list_pdfs():
    files = []
    for file in os.listdir(arxiv_download_dir):
        if file.endswith(".pdf"):
            files.append(os.path.join(arxiv_download_dir, file))
    return files


def clean_for_filename(string):
    assert string, "String is empty"
    string = string.strip().lower()
    return re.sub(r"[^a-z0-9\._-]", "_", string)


def paper_is_downloaded(paper_id):
    assert paper_id, "Paper ID is empty"
    paper_id = clean_for_filename(paper_id)

    pdfs = list_pdfs()
    for pdf in pdfs:
        if os.path.basename(pdf).startswith(paper_id):
            return pdf
    return False


def paper_is_processed(paper_id):
    assert paper_id, "Paper ID is empty"
    paper_id = clean_for_filename(paper_id)

    for name in os.listdir(arxiv_processed_dir):
        dir_path = os.path.join(arxiv_processed_dir, name)
        if os.path.isdir(dir_path) and name.startswith(paper_id):
            return dir_path
    return False


def get_paper_filename(paper_id, paper_title):
    assert paper_id, "Paper ID is empty"
    assert paper_title, "Paper title is empty"
    paper_id = clean_for_filename(paper_id)
    paper_title = clean_for_filename(paper_title)
    return f"{paper_id}_{paper_title}.pdf"


def default_callback(status: str):
    print(status)


def download_paper(
    paper_id,
    download_source=False,
    extract_source=False,
    callback: callable = default_callback,
) -> str:
    assert paper_id, "Paper ID is empty"
    assert not paper_is_downloaded(paper_id), "Paper already downloaded"

    callback("Searching paper on arXiv...")
    client = arxiv.Client()
    results = list(client.results(arxiv.Search(id_list=[paper_id])))
    assert len(results) == 1, "Paper not found"
    paper_result = results[0]
    callback("OK")

    callback("Downloading PDF...")
    file_name = get_paper_filename(paper_id, paper_result.title)
    print(f"Downloading PDF {file_name}...")
    paper_result.download_pdf(arxiv_download_dir, file_name, "arxiv.org")  # todo
    assert paper_is_downloaded(paper_id), "Paper not downloaded"
    callback("OK")
    if not download_source:
        return os.path.join(arxiv_download_dir, file_name)

    callback("Downloading source...")
    file_name = file_name.replace(".pdf", ".tar.gz")
    print(f"Downloading source {file_name}...")
    paper_result.download_source(arxiv_download_dir, file_name, "arxiv.org")  # todo
    callback("OK")
    if not extract_source:
        return os.path.join(arxiv_download_dir, file_name)

    callback("Extracting source...")
    extraction_dir = file_name.replace(".tar.gz", "")
    extraction_dir = os.path.join(arxiv_download_dir, extraction_dir)
    assert not os.path.exists(extraction_dir), "Extraction directory already exists"
    os.makedirs(extraction_dir)

    file_name = os.path.join(arxiv_download_dir, file_name)
    print(f"Extracting {file_name} to {extraction_dir}...")
    extract_compressed_archive(file_name, extraction_dir)
    callback("OK")
    return os.path.join(arxiv_download_dir, file_name)


def extract_compressed_archive(file_path_compressed, extraction_dir):
    import tarfile
    import gzip
    import shutil

    def extract_tar_gz():
        with tarfile.open(file_path_compressed, "r:*") as tar:
            tar.extractall(path=extraction_dir)
            tar.close()

    def get_gzip_original_filename(path):
        try:
            with open(path, "rb") as f:
                f.seek(3)  # skip ID1, ID2, CM
                flg = ord(f.read(1))
                f.seek(6, 1)  # skip MTIME, XFL, OS
                if flg & 0x08:  # FNAME flag
                    name = []
                    while True:
                        b = f.read(1)
                        if b == b"\x00":
                            break
                        name.append(b)
                    return b"".join(name).decode("utf-8")
        except:
            pass
        return None

    def extract_gz():
        out_file = get_gzip_original_filename(file_path_compressed) or "file.txt"
        out_file = os.path.join(extraction_dir, out_file)

        with gzip.open(file_path_compressed, "rb") as f_in:
            with open(out_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    try:
        extract_tar_gz()
    except:
        try:
            extract_gz()
        except:
            raise Exception(f"Failed to extract {file_path_compressed}")


def process_pdf(pdf_path, callback: callable = default_callback):
    from magic_pdf.data.data_reader_writer import (
        FileBasedDataWriter,
        FileBasedDataReader,
    )
    from magic_pdf.data.dataset import PymuDocDataset
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
    from magic_pdf.config.enums import SupportedPdfParseMethod

    # create output directory
    callback("Creating output directory...")
    base_name = os.path.basename(pdf_path)
    base_name = base_name.replace(".pdf", "")
    out_dir = os.path.join(arxiv_processed_dir, base_name)
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
    callback("Processing PDF...")
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
