from functools import lru_cache

from app.core.config import settings


@lru_cache
def get_embedding_model():
    from FlagEmbedding import BGEM3FlagModel

    return BGEM3FlagModel(
        settings.embedding_model_name,
        devices=settings.embedding_device,
        use_fp16=settings.embedding_device.startswith("cuda"),
    )


def embed_query(text: str) -> dict[str, object]:
    model = get_embedding_model()

    output = model.encode(
        [text],
        batch_size=1,
        max_length=512,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )

    return {
        "dense": output["dense_vecs"][0].tolist(),
        "sparse": output["lexical_weights"][0],
    }
