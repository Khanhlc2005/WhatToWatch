from functools import lru_cache

from app.core.config import settings
from app.core.device import resolve_device


@lru_cache
def get_embedding_model():
    from FlagEmbedding import BGEM3FlagModel
    device = resolve_device(settings.embedding_device)
    if device == "cpu":
        import torch
        torch.set_num_threads(max(1, settings.embedding_cpu_threads))

    return BGEM3FlagModel(
        settings.embedding_model_path or settings.embedding_model_name,
        devices=device,
        use_fp16=device.startswith("cuda"),
    )


@lru_cache(maxsize=512)
def embed_query(text: str) -> dict[str, object]:
    model = get_embedding_model()

    output = model.encode(
        [text],
        batch_size=1,
        max_length=128,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )

    return {
        "dense": output["dense_vecs"][0].tolist(),
        "sparse": output["lexical_weights"][0],
    }
