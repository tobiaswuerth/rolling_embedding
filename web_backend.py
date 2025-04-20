from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import elasticsearch
from elasticsearch import Elasticsearch
import latexcodec
import traceback
import os

from rolling.arxiv import (
    download_pdf,
    pdf_is_downloaded,
)
from rolling.processing import (
    process_pdf,
    pdf_is_processed,
    structurize_pdf,
    pdf_is_structurized,
    load_document,
    delete_pdf_structurized,
    ARXIV_DIR_PDF_PROCESSED,
)

from rolling.embedding import GTEEmbeddingModel


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="*")

client = Elasticsearch(
    hosts="http://localhost:9200/",
    api_key="a1VxLUZaWUJ6Q1VRYXlSWTJSX2U6RWx3X0xQbXZURnlsNGU5UmNFeWZhZw==",
)

model = GTEEmbeddingModel()


def get_paper_by_id(paper_id):
    response = client.get(index="arxiv", id=paper_id)
    paper = response["_source"]
    paper["authors"] = paper["authors"].encode("utf-8").decode("latex")
    paper["submitter"] = paper["submitter"].encode("utf-8").decode("latex")
    paper["title"] = paper["title"].encode("utf-8").decode("latex")
    paper["abstract"] = paper["abstract"].encode("utf-8").decode("latex")
    return paper


@socketio.on("connect")
def handle_connect():
    print("SocketIO: client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("SocketIO: client disconnected")


@socketio.on_error()
def handle_socketio_error(e):
    print("SocketIO Error:", e)
    traceback.print_exc()
    emit("error", {"error": str(e)})


def socketio_callback_progress(status):
    emit("progress", {"status": status})


@socketio.on("paper_1_download")
def paper_1_download(data):
    paper_id = data["paper_id"]
    download_pdf(paper_id, callback=socketio_callback_progress)
    emit("done")


@socketio.on("paper_2_process")
def paper_2_process(data):
    paper_id = data["paper_id"]
    process_pdf(paper_id, callback=socketio_callback_progress)
    emit("done")


@socketio.on("paper_3_structurize")
def paper_3_structurize(data):
    paper_id = data["paper_id"]
    structurize_pdf(paper_id, callback=socketio_callback_progress)
    emit("done")


@app.errorhandler(404)
def handle_404(e):
    print("404 Error:", e)
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(elasticsearch.NotFoundError)
def handle_404_elastic(e):
    return handle_404(e)


@app.errorhandler(Exception)
def handle_error(e):
    print("Error:", e)
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


@app.route("/search_by_text", methods=["POST"])
def _search_by_text():
    print(f"Received request: {request.json}")

    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query not provided"}), 400

    response = client.search(
        index="arxiv",
        query={
            "match_phrase": {
                "title": query,
            },
        },
    )

    return jsonify(response["hits"]["hits"])


@app.route("/search_by_embedding", methods=["POST"])
def _search_by_embedding():
    print(f"Received request: {request.json}")

    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query not provided"}), 400

    emb = model.encode(query)[0]

    response = client.search(
        index="arxiv",
        query={
            "knn": {
                "field": "embedding",
                "query_vector": emb,
            },
        },
    )

    return jsonify(response["hits"]["hits"])


@app.route("/paper_by_id_and_knn", methods=["POST"])
def _paper_by_id_and_knn():
    print(f"Received request: {request.json}")

    paper_id = request.json.get("paper_id", "")
    if not paper_id:
        return jsonify({"error": "Paper ID not provided"}), 400

    # 1. get paper by id
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    emb = paper.get("embedding")

    # 2. calc pagination
    # note, since we use KNN afterwards pagination technically doesn't work because you cannot skip before you cluster
    # nevertheless, one might want to fetch more later on in the process, therefore requiring re-execution - suboptimal, I know
    page = request.json.get("page", 1)
    page_size = 10
    from_value = (page - 1) * page_size

    # 3. find similar papers by KNN on embedding
    knn_response = client.search(
        index="arxiv",
        query={
            "bool": {
                "must": [
                    {
                        "knn": {
                            "field": "embedding",
                            "query_vector": emb,
                            "k": (page * page_size)
                            + 1,  # +1 because self is excluded afterwards
                        }
                    }
                ],
                "must_not": [
                    {
                        "term": {
                            "_id": paper_id,
                        },
                    },
                ],
            }
        },
        from_=from_value,
        size=page_size,
    )

    matches = knn_response["hits"]["hits"]

    results = {"paper": paper, "matches": matches}
    return jsonify(results)


@app.route("/paper_by_id", methods=["POST"])
def _paper_by_id():
    print(f"Received request: {request.json}")

    paper_id = request.json.get("paper_id", "")
    if not paper_id:
        return jsonify({"error": "Paper ID not provided"}), 400

    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    return jsonify(
        {
            "paper": paper,
            "is_downloaded": True if pdf_is_downloaded(paper_id) else False,
            "is_processed": True if pdf_is_processed(paper_id) else False,
            "is_structurized": True if pdf_is_structurized(paper_id) else False,
        }
    )


@app.route("/load_document_by_id", methods=["POST"])
def _load_document_by_id():
    print(f"Received request: {request.json}")

    paper_id = request.json.get("paper_id", "")
    if not paper_id:
        return jsonify({"error": "Paper ID not provided"}), 400

    proc_dir = pdf_is_processed(paper_id)
    if not proc_dir:
        return jsonify({"error": "Paper not processed"}), 404
    
    if not pdf_is_structurized(paper_id):
        return jsonify({"error": "Paper not structurized"}), 404

    doc = load_document(proc_dir)

    return jsonify(
        {
            "contents": doc,
        }
    )

@app.route("/delete_document_by_id", methods=["DELETE"])
def _delete_document_by_id():
    print(f"Received request: {request.json}")

    paper_id = request.json.get("paper_id", "")
    if not paper_id:
        return jsonify({"error": "Paper ID not provided"}), 400

    delete_pdf_structurized(paper_id)
    return jsonify()


@app.route("/img/<path:path>", methods=["GET"])
def _img(path):
    assert path, "Path is empty"
    assert os.path.exists(path), "Path does not exist"
    assert ARXIV_DIR_PDF_PROCESSED in path, "Path is not in ARXIV_DIR_PDF_PROCESSED"

    with open(path, "rb") as f:
        img = f.read()
    return img, 200, {"Content-Type": "image/jpeg"}


if __name__ == "__main__":
    socketio.run(app, port=3001, debug=True)
