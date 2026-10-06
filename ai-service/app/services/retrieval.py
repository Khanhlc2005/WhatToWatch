import math

from qdrant_client import models

from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.schemas.retrieval import (
    MovieSearchHit,
    MovieSearchRequest,
    MovieSearchResponse,
    SampleMoviePoint,
    SampleRetrievalResponse,
)
from app.services.embedding import embed_query
from app.services.filters import build_payload_filter


def fetch_sample_movies(limit: int = 5) -> SampleRetrievalResponse:
    client = get_qdrant_client()

    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return SampleRetrievalResponse(
        collection=settings.qdrant_collection,
        count=len(points),
        points=[
            SampleMoviePoint(
                id=str(point.id),
                title=point.payload.get("title"),
                imdb_id=point.payload.get("imdb_id"),
                year=point.payload.get("year"),
            )
            for point in points
        ],
    )


def search_movies(request: MovieSearchRequest) -> MovieSearchResponse:
    vectors = embed_query(request.query)
    if request.mode == "dense":
        query = vectors["dense"]
        if len(query) != 1024 or not all(math.isfinite(v) for v in query) or not any(query):
            raise ValueError("Invalid BGE-M3 dense vector")
    else:
        pairs = sorted((int(token), float(weight)) for token, weight in vectors["sparse"].items())
        if any(token < 0 or not math.isfinite(weight) for token, weight in pairs):
            raise ValueError("Invalid BGE-M3 sparse vector")
        pairs = [(token, weight) for token, weight in pairs if weight != 0]
        if not pairs:
            return MovieSearchResponse(collection=settings.qdrant_collection, mode=request.mode, hits=[])
        query = models.SparseVector(indices=[p[0] for p in pairs], values=[p[1] for p in pairs])

    result = get_qdrant_client().query_points(
        collection_name=settings.qdrant_collection,
        query=query,
        using=request.mode,
        query_filter=build_payload_filter(request.filters),
        limit=request.limit,
        with_payload=True,
        with_vectors=False,
    )
    hits = []
    seen = set()
    for point in sorted(result.points, key=lambda point: (-point.score, str(point.id))):
        payload = point.payload or {}
        raw_id = payload.get("movie_id")
        valid_id = type(raw_id) is int and 0 < raw_id <= 2**63 - 1
        if valid_id:
            identity = ("movie", raw_id)
        elif payload.get("imdb_id"):
            identity = ("imdb", payload["imdb_id"])
        else:
            identity = ("point", str(point.id))
        if identity in seen:
            continue
        seen.add(identity)
        hits.append(MovieSearchHit(
            point_id=str(point.id),
            movie_id=raw_id if valid_id else None,
            imdb_id=payload.get("imdb_id"),
            tmdb_id=payload.get("tmdb_id"),
            title=payload.get("title"),
            score=point.score,
            id_status="present_unverified" if valid_id else "missing" if raw_id is None else "invalid",
        ))
    return MovieSearchResponse(collection=settings.qdrant_collection, mode=request.mode, hits=hits)
