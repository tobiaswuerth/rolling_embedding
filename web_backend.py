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


if __name__ == "__main__":
    app.run(port=3001, debug=True)
