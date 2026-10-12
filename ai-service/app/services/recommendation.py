"""Content candidates from an existing profile with optional final ranking."""

import logging
import math

from qdrant_client import models

from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.schemas.recommendation import (
    RecommendationHit,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationReason,
    ScoreComponents,
)
from app.services.filters import build_payload_filter
from app.services.preference import PROFILE_VERSION, normalize

logger = logging.getLogger(__name__)


def _final_hit(movie_id: int, cosine: float, rating: object) -> RecommendationHit:
    similarity = max(0.0, min(1.0, (cosine + 1) / 2))
    imdb = (float(rating) / 10 if type(rating) in (int, float)
            and math.isfinite(rating) and 0 <= rating <= 10 else None)
    similarity_weight = settings.recommendation_similarity_weight
    imdb_weight = settings.recommendation_imdb_weight if imdb is not None else 0.0
    if (not all(math.isfinite(value) and value >= 0 for value in (similarity_weight, imdb_weight))
            or similarity_weight + imdb_weight <= 0):
        raise ValueError("Invalid recommendation ranking weights")
    total = similarity_weight + imdb_weight
    weights = {"profile_similarity": similarity_weight / total,
               "imdb_rating": imdb_weight / total}
    score = weights["profile_similarity"] * similarity + weights["imdb_rating"] * (imdb or 0)
    reasons = []
    if weights["profile_similarity"] > 0 and cosine > 0:
        reasons.append(RecommendationReason(code="profile_similarity", value=similarity))
    if weights["imdb_rating"] > 0 and imdb is not None:
        reasons.append(RecommendationReason(code="imdb_rating", value=imdb))
    return RecommendationHit(movie_id=movie_id, score=score,
        score_components=ScoreComponents(profile_similarity=similarity, imdb_rating=imdb,
                                          weights=weights), reasons=reasons)


def recommend_movies(request: RecommendationRequest) -> RecommendationResponse:
    client = get_qdrant_client()
    profiles = client.retrieve(
        collection_name=settings.qdrant_user_profiles_collection,
        ids=[request.user_id], with_payload=True, with_vectors=["dense"],
    )
    if not profiles:
        return RecommendationResponse(user_id=request.user_id, status="cold_start", hits=[])
    profile = profiles[0]
    payload = profile.payload or {}
    vector = normalize(profile.vector.get("dense") if isinstance(profile.vector, dict) else None)
    if (type(payload.get("user_id")) is not int or payload["user_id"] != request.user_id
            or payload.get("profile_version") != PROFILE_VERSION or vector is None):
        raise ValueError("Invalid or incompatible user profile")

    query_filter = build_payload_filter(request.filters)
    excluded = set(request.exclude_movie_ids)
    if excluded:
        query_filter = query_filter or models.Filter()
        query_filter.must_not = list(query_filter.must_not or []) + [models.FieldCondition(
            key="movie_id", match=models.MatchAny(any=sorted(excluded))
        )]
    # Bounded overfetch allows duplicates/invalid IDs without an unbounded catalog scan.
    candidates = client.query_points(
        collection_name=settings.qdrant_collection, query=vector, using="dense",
        query_filter=query_filter, limit=max(50, 5 * request.limit),
        with_payload=["movie_id", "rating"] if request.ranking == "final" else ["movie_id"],
        with_vectors=False,
    ).points
    scores = {}
    for point in candidates:
        movie_id = (point.payload or {}).get("movie_id")
        if (type(movie_id) is not int or not 0 < movie_id <= 2**63 - 1
                or movie_id in excluded or not math.isfinite(point.score)):
            continue
        if movie_id not in scores or point.score > scores[movie_id][0]:
            scores[movie_id] = (point.score, (point.payload or {}).get("rating"))
    if request.ranking == "final":
        hits = [_final_hit(movie_id, score, rating)
                for movie_id, (score, rating) in scores.items()]
        hits.sort(key=lambda hit: (-hit.score, hit.movie_id))
        hits = hits[:request.limit]
        for hit in hits:
            logger.info("recommendation_score_components user_id=%s movie_id=%s score=%s components=%s",
                        request.user_id, hit.movie_id, hit.score,
                        hit.score_components.model_dump())
    else:
        hits = [RecommendationHit(movie_id=movie_id, score=score)
                for movie_id, (score, _) in sorted(scores.items(), key=lambda item: (-item[1][0], item[0]))[:request.limit]]
    return RecommendationResponse(user_id=request.user_id, status="ready", hits=hits)
