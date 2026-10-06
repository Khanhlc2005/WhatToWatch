import os

from qdrant_client import QdrantClient, models


def ensure_collection(client, name, with_sparse):
    if not client.collection_exists(name):
        options = {}

        if with_sparse:
            options["sparse_vectors_config"] = {
                "sparse": models.SparseVectorParams()
            }

        client.create_collection(
            collection_name=name,
            vectors_config={
                "dense": models.VectorParams(
                    size=1024,
                    distance=models.Distance.COSINE,
                )
            },
            **options,
        )

        print(f"Created: {name}")
        return

    params = client.get_collection(name).config.params
    vectors = params.vectors

    if not isinstance(vectors, dict) or "dense" not in vectors:
        raise ValueError(f"{name}: thiếu named vector dense")

    if vectors["dense"].size != 1024:
        raise ValueError(f"{name}: dense dimension phải bằng 1024")

    if vectors["dense"].distance != models.Distance.COSINE:
        raise ValueError(f"{name}: dense distance phải là Cosine")

    if with_sparse and "sparse" not in (params.sparse_vectors or {}):
        raise ValueError(f"{name}: thiếu named vector sparse")

    print(f"Schema OK: {name}")


def main():
    client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        timeout=60,
    )

    ensure_collection(client, "movies", with_sparse=True)
    ensure_collection(client, "user_profiles", with_sparse=False)


if __name__ == "__main__":
    main()