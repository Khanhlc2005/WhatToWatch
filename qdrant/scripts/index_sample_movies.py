import hashlib
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient, models


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/seeds/movies_cleaned_sample.jsonl"

MODEL_NAME = "BAAI/bge-m3"
COLLECTION = os.environ["QDRANT_COLLECTION"]
QDRANT_URL = os.environ["QDRANT_URL"]
DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda:0")

MAX_LENGTH = 512
BATCH_SIZE = 1
EMBEDDING_VERSION = "bge-m3_movie_text_v1_len512_v1"


def point_id(imdb_id):
    # Cùng IMDb ID luôn tạo cùng UUID.
    return str(uuid5(NAMESPACE_URL, f"whattowatch:movie:{imdb_id}"))


def sparse_vector(weights):
    pairs = sorted(
        (int(token_id), float(weight))
        for token_id, weight in weights.items()
        if float(weight) != 0.0
    )

    if not pairs:
        raise ValueError("Sparse vector rỗng")

    if not all(np.isfinite(weight) for _, weight in pairs):
        raise ValueError("Sparse vector chứa NaN/Inf")

    return models.SparseVector(
        indices=[token_id for token_id, _ in pairs],
        values=[weight for _, weight in pairs],
    )


def make_payload(movie):
    release_date = movie.get("release_date")
    year = (
        int(release_date[:4])
        if release_date
        else movie.get("imdb_year")
    )

    return {
        "movie_id": movie.get("movie_id"),
        "imdb_id": movie["imdb_id"],
        "tmdb_id": movie["tmdb_id"],
        "title": movie["title"],
        "genres": [item["name"] for item in movie.get("genres", [])],
        "keywords": [
            item["name"] for item in movie.get("keywords", [])
        ],
        "year": year,
        "rating": movie.get("imdb_rating"),
        "language": movie.get("original_language"),
        "country": [
            item["iso_3166_1"]
            for item in movie.get("production_countries", [])
        ],
        "runtime": movie.get("runtime_minutes"),
        "adult": movie.get("adult"),
        "status": movie.get("status"),
        "text_template_version": movie["text_template_version"],
        "embedding_model": MODEL_NAME,
        "embedding_version": EMBEDDING_VERSION,
        "text_sha256": hashlib.sha256(
            movie["embedding_text"].encode("utf-8")
        ).hexdigest(),
    }


def ensure_collection(client, dimension):
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "dense": models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams()
            },
        )
        return

    # Collection đã có: kiểm tra schema, không xóa dữ liệu.
    params = client.get_collection(COLLECTION).config.params
    vectors = params.vectors

    if not isinstance(vectors, dict) or "dense" not in vectors:
        raise ValueError("Collection thiếu named vector 'dense'")

    if vectors["dense"].size != dimension:
        raise ValueError("Dimension collection không khớp model")

    if vectors["dense"].distance != models.Distance.COSINE:
        raise ValueError("Collection không dùng Cosine")

    if "sparse" not in (params.sparse_vectors or {}):
        raise ValueError("Collection thiếu named vector 'sparse'")


def main():
    movies = [
        json.loads(line)
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not movies:
        raise ValueError("Không có phim đầu vào")

    imdb_ids = [movie["imdb_id"] for movie in movies]
    if len(imdb_ids) != len(set(imdb_ids)):
        raise ValueError("Input có IMDb ID trùng")

    texts = [movie["embedding_text"] for movie in movies]
    if not all(isinstance(text, str) and text.strip() for text in texts):
        raise ValueError("Có embedding_text rỗng")

    # Kiểm tra Qdrant trước khi tải model.
    client = QdrantClient(url=QDRANT_URL, timeout=60)
    client.get_collections()

    print(f"Loading {MODEL_NAME} on {DEVICE}...", flush=True)
    model = BGEM3FlagModel(
        MODEL_NAME,
        devices=DEVICE,
        use_fp16=DEVICE.startswith("cuda"),
    )

    # Không âm thầm cắt mất phần cuối canonical text.
    for movie, text in zip(movies, texts):
        token_count = len(
            model.tokenizer(
                text,
                add_special_tokens=True,
                truncation=False,
            )["input_ids"]
        )
        if token_count > MAX_LENGTH:
            raise ValueError(
                f"{movie['title']}: {token_count} tokens > {MAX_LENGTH}. "
                "Tăng MAX_LENGTH và đổi EMBEDDING_VERSION."
            )

    output = model.encode(
        texts,
        batch_size=1,
        max_length=512,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )

    dense = np.asarray(output["dense_vecs"], dtype=np.float32)

    if dense.shape != (len(movies), 1024):
        raise ValueError(f"Dense shape không đúng: {dense.shape}")

    if not np.isfinite(dense).all():
        raise ValueError("Dense vectors chứa NaN/Inf")

    if np.any(np.linalg.norm(dense, axis=1) == 0):
        raise ValueError("Có dense vector toàn số 0")

    if len(output["lexical_weights"]) != len(movies):
        raise ValueError("Số sparse vectors không khớp số phim")

    ensure_collection(client, dense.shape[1])

    points = [
        models.PointStruct(
            id=point_id(movie["imdb_id"]),
            vector={
                "dense": dense[index].tolist(),
                "sparse": sparse_vector(
                    output["lexical_weights"][index]
                ),
            },
            payload=make_payload(movie),
        )
        for index, movie in enumerate(movies)
    ]

    before = client.count(
        collection_name=COLLECTION, exact=True
    ).count

    client.upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True,
    )

    after = client.count(
        collection_name=COLLECTION, exact=True
    ).count

    stored = client.retrieve(
        collection_name=COLLECTION,
        ids=[point.id for point in points],
        with_payload=True,
        with_vectors=True,
    )

    expected = {str(point.id): point for point in points}

    if len(stored) != len(points):
        raise ValueError("Không retrieve đủ sample points")

    for record in stored:
        original = expected[str(record.id)]
        assert record.payload == original.payload
        assert len(record.vector["dense"]) == 1024
        assert "sparse" in record.vector

    report = {
        "collection": COLLECTION,
        "model": MODEL_NAME,
        "device": DEVICE,
        "embedding_version": EMBEDDING_VERSION,
        "dense_shape": list(dense.shape),
        "input_count": len(movies),
        "count_before": before,
        "count_after": after,
        "retrieved_count": len(stored),
        "missing_mysql_movie_ids": sum(
            movie.get("movie_id") is None for movie in movies
        ),
    }

    # Giữ cả lần chạy đầu và lần chạy lại để chứng minh idempotency.
    evidence = ROOT / "docs/evidence/week-02"
    evidence.mkdir(parents=True, exist_ok=True)

    with (evidence / "issue-8-index-runs.jsonl").open(
        "a", encoding="utf-8"
    ) as file:
        file.write(json.dumps(report, ensure_ascii=False) + "\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()