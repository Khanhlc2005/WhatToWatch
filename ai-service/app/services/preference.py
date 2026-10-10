"""Derived profiles from complete rating snapshots; MySQL remains authoritative."""

import math
from datetime import datetime, timezone

from qdrant_client import models

from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.schemas.preference import PreferenceResponse, PreferenceSnapshot, SkippedMovie

PROFILE_VERSION = "ratings-v1"
DIMENSION = 1024
MIN_RATINGS = 3


def normalize(vector):
    if not isinstance(vector, list) or len(vector) != DIMENSION:
        return None
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
        return None
    norm = math.hypot(*vector)
    if not math.isfinite(norm) or norm <= 1e-12:
        return None
    return [value / norm for value in vector]


def rating_weight(rating: float) -> float:
    signal = (rating - 3.0) / 2.0
    return signal if signal >= 0 else 0.35 * signal


def rebuild_preference(snapshot: PreferenceSnapshot) -> PreferenceResponse:
    client = get_qdrant_client()
    total = [0.0] * DIMENSION
    usable = 0
    skipped = []
    # Stable summation order makes replays independent of snapshot ordering.
    for rating in sorted(snapshot.ratings, key=lambda item: item.movie_id):
        weight = rating_weight(rating.rating)
        if weight == 0:
            continue
        points, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=models.Filter(must=[models.FieldCondition(
                key="movie_id", match=models.MatchValue(value=rating.movie_id)
            )]),
            limit=2, with_vectors=["dense"], with_payload=["movie_id"],
        )
        reason = None
        vector = None
        if not points:
            reason = "missing_embedding"
        elif len(points) > 1:
            reason = "ambiguous_movie_id"
        else:
            point = points[0]
            payload_id = (point.payload or {}).get("movie_id")
            vector = normalize(point.vector.get("dense") if isinstance(point.vector, dict) else None)
            if type(payload_id) is not int or payload_id != rating.movie_id or vector is None:
                reason = "invalid_embedding"
        if reason:
            skipped.append(SkippedMovie(movie_id=rating.movie_id, reason=reason))
            continue
        usable += 1
        total = [value + weight * component for value, component in zip(total, vector)]

    profile = normalize(total)
    reason = "insufficient_ratings" if usable < MIN_RATINGS else "zero_vector" if profile is None else None
    response = PreferenceResponse(
        user_id=snapshot.user_id, status="cold_start" if reason else "ready", reason=reason,
        profile_version=PROFILE_VERSION, last_updated=datetime.now(timezone.utc).isoformat(),
        rating_count=len(snapshot.ratings), usable_rating_count=usable, skipped_movies=skipped,
    )
    # Only mutate after all reads succeed. No zero vector or stale warm profile.
    if reason:
        client.delete(collection_name=settings.qdrant_user_profiles_collection,
                      points_selector=models.PointIdsList(points=[snapshot.user_id]), wait=True)
    else:
        client.upsert(collection_name=settings.qdrant_user_profiles_collection, points=[
            models.PointStruct(id=snapshot.user_id, vector={"dense": profile}, payload={
                "user_id": snapshot.user_id, "profile_version": PROFILE_VERSION,
                "last_updated": response.last_updated,
            })
        ], wait=True)
    return response
