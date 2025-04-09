from flask import Flask, request, jsonify
from flask_cors import CORS
from elasticsearch import Elasticsearch
from rolling.embedding import GTEEmbeddingModel

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

client = Elasticsearch(
    hosts="http://localhost:9200/",
    api_key="a1VxLUZaWUJ6Q1VRYXlSWTJSX2U6RWx3X0xQbXZURnlsNGU5UmNFeWZhZw==",
)

model = GTEEmbeddingModel()


@app.route("/search_by_text", methods=["POST"])
def search_by_text():
    try:
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

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return jsonify({"error": "Error querying Elasticsearch"}), 500


@app.route("/search_by_embedding", methods=["POST"])
def search_by_embedding():
    try:
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

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return jsonify({"error": "Error querying Elasticsearch"}), 500


@app.route("/search_by_paper_id", methods=["POST"])
def search_by_paper_id():
    try:
        print(f"Received request: {request.json}")

        paper_id = request.json.get("paper_id", "")
        if not paper_id:
            return jsonify({"error": "Paper ID not provided"}), 400

        # 1. get paper by id
        response = client.get(index="arxiv", id=paper_id)
        paper = response.get("_source", None)
        if not paper:
            return jsonify({"error": "Paper not found"}), 404

        emb = paper.get("embedding")

        # 2. calc pagination
        # note, since we use KNN afterwards pagination technically doesn't work because you cannot skip before you cluster
        # nevertheless, one might want to fetch more later on in the process, therefor requiring re-execution - suboptimal, I know
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
                                "k": (page * page_size) + 1,  # +1 because self is excluded afterwards
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

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return jsonify({"error": "Error querying Elasticsearch"}), 500


if __name__ == "__main__":
    app.run(port=3001, debug=True)
