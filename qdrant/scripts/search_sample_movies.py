import json
from pathlib import Path

from index_sample_movies import (
    COLLECTION,
    DEVICE,
    MAX_LENGTH,
    MODEL_NAME,
    QDRANT_URL,
    sparse_vector,
)
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient


QUERIES = [
    "a movie about space travel and a father daughter relationship",
    "a movie about an Italian American mafia family",
    "a movie about an underground fight club",
]


def main():
    client = QdrantClient(url=QDRANT_URL, timeout=60)
    model = BGEM3FlagModel(
        MODEL_NAME,
        devices=DEVICE,
        use_fp16=DEVICE.startswith("cuda"),
    )

    report = []

    for query in QUERIES:
        output = model.encode(
            [query],
            batch_size=1,
            max_length=MAX_LENGTH,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )

        vectors = {
            "dense": output["dense_vecs"][0].tolist(),
            "sparse": sparse_vector(output["lexical_weights"][0]),
        }

        for branch, vector in vectors.items():
            hits = client.query_points(
                collection_name=COLLECTION,
                query=vector,
                using=branch,
                limit=3,
                with_payload=True,
            ).points

            result = {
                "query": query,
                "branch": branch,
                "hits": [
                    {
                        "title": hit.payload["title"],
                        "imdb_id": hit.payload["imdb_id"],
                        "score": hit.score,
                    }
                    for hit in hits
                ],
            }

            report.append(result)
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()