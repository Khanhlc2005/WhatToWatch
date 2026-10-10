"""Content candidates from an existing profile; no embedding inference or reranking."""

import math

from qdrant_client import models

from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.schemas.recommendation import RecommendationHit, RecommendationRequest, RecommendationResponse
from app.services.filters import build_payload_filter
from app.services.preference import PROFILE_VERSION, normalize


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
        with_payload=["movie_id"], with_vectors=False,
    ).points
    scores = {}
    for point in candidates:
        movie_id = (point.payload or {}).get("movie_id")
        if (type(movie_id) is not int or not 0 < movie_id <= 2**63 - 1
                or movie_id in excluded or not math.isfinite(point.score)):
            continue
        scores[movie_id] = max(scores.get(movie_id, -math.inf), point.score)
    hits = [RecommendationHit(movie_id=movie_id, score=score)
            for movie_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:request.limit]]
    return RecommendationResponse(user_id=request.user_id, status="ready", hits=hits)
