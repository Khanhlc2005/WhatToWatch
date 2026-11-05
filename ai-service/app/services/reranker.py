"""Lazy BGE cross encoder adapter; loading happens only for opted-in requests."""

import math
from functools import lru_cache

from app.core.config import settings
from app.core.device import resolve_device


@lru_cache(maxsize=1)
def get_reranker():
    from FlagEmbedding import FlagReranker

    device = resolve_device(settings.reranker_device)
    return FlagReranker(
        settings.reranker_model_path or settings.reranker_model_name,
        devices=device,
        use_fp16=device.startswith("cuda"),
    )


def score_pairs(query: str, documents: list[str]) -> list[float]:
    if not documents:
        return []
    scores = get_reranker().compute_score([[query, document] for document in documents], batch_size=8)
    try:
        iter(scores)
    except TypeError:
        scores = [scores]
    scores = [float(score) for score in scores]
    if len(scores) != len(documents) or not all(math.isfinite(score) for score in scores):
        raise ValueError("Invalid reranker scores")
    return scores
