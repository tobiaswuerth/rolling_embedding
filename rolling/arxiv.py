import re
import os
import arxiv


ARXIV_DIR_PDF_DOWNLOADS = "./arxiv_downloads"


def clean_for_filename(string):
    assert string, "String is empty"
    string = string.strip().lower()
    return re.sub(r"[^a-z0-9\._-]", "_", string)


def list_pdfs():
    files = []
    for file in os.listdir(ARXIV_DIR_PDF_DOWNLOADS):
        if file.endswith(".pdf"):
            files.append(os.path.join(ARXIV_DIR_PDF_DOWNLOADS, file))
    return files


def paper_is_downloaded(paper_id):
    assert paper_id, "Paper ID is empty"
    paper_id = clean_for_filename(paper_id)

    pdfs = list_pdfs()
    for pdf in pdfs:
        if os.path.basename(pdf).startswith(paper_id):
            return pdf
    return False


def get_paper_filename(paper_id, paper_title):
    assert paper_id, "Paper ID is empty"
    assert paper_title, "Paper title is empty"
    paper_id = clean_for_filename(paper_id)
    paper_title = clean_for_filename(paper_title)
    return f"{paper_id}_{paper_title}.pdf"


def download_paper(
    paper_id,
    download_source=False,
    extract_source=False,
    callback: callable = print,
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
    paper_result.download_pdf(ARXIV_DIR_PDF_DOWNLOADS, file_name, "arxiv.org")  # todo
    assert paper_is_downloaded(paper_id), "Paper not downloaded"
    callback("OK")
    if not download_source:
        return os.path.join(ARXIV_DIR_PDF_DOWNLOADS, file_name)

    callback("Downloading source...")
    file_name = file_name.replace(".pdf", ".tar.gz")
    print(f"Downloading source {file_name}...")
    paper_result.download_source(
        ARXIV_DIR_PDF_DOWNLOADS, file_name, "arxiv.org"
    )  # todo
    callback("OK")
    if not extract_source:
        return os.path.join(ARXIV_DIR_PDF_DOWNLOADS, file_name)

    callback("Extracting source...")
    extraction_dir = file_name.replace(".tar.gz", "")
    extraction_dir = os.path.join(ARXIV_DIR_PDF_DOWNLOADS, extraction_dir)
    assert not os.path.exists(extraction_dir), "Extraction directory already exists"
    os.makedirs(extraction_dir)

    file_name = os.path.join(ARXIV_DIR_PDF_DOWNLOADS, file_name)
    print(f"Extracting {file_name} to {extraction_dir}...")
    extract_compressed_archive(file_name, extraction_dir)
    callback("OK")
    return os.path.join(ARXIV_DIR_PDF_DOWNLOADS, file_name)


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
