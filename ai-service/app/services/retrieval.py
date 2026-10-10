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

RRF_K = 60


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
    queries = {}
    if request.mode in ("dense", "hybrid"):
        dense = vectors["dense"]
        if len(dense) != 1024 or not all(math.isfinite(v) for v in dense) or not any(dense):
            raise ValueError("Invalid BGE-M3 dense vector")
        queries["dense"] = dense
    if request.mode in ("sparse", "hybrid"):
        pairs = sorted((int(token), float(weight)) for token, weight in vectors["sparse"].items())
        if any(token < 0 or not math.isfinite(weight) for token, weight in pairs):
            raise ValueError("Invalid BGE-M3 sparse vector")
        pairs = [(token, weight) for token, weight in pairs if weight != 0]
        if not pairs and request.mode == "sparse":
            return MovieSearchResponse(collection=settings.qdrant_collection, mode=request.mode, hits=[])
        if pairs:
            queries["sparse"] = models.SparseVector(
                indices=[p[0] for p in pairs], values=[p[1] for p in pairs]
            )

    client = get_qdrant_client()
    query_filter = build_payload_filter(request.filters)
    results = {}
    for mode, query in queries.items():
        result = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query,
            using=mode,
            query_filter=query_filter,
            limit=request.limit,
            with_payload=True,
            with_vectors=False,
        )
        results[mode] = sorted(result.points, key=lambda point: (-point.score, str(point.id)))

    if request.mode == "hybrid":
        ranked = _fuse_rrf(results, request.limit)
    else:
        ranked = ((point, point.score) for point in results[request.mode])
    hits = []
    seen = set()
    for point, score in ranked:
        payload = point.payload or {}
        identity = _identity(point)
        if identity in seen:
            continue
        seen.add(identity)
        raw_id = payload.get("movie_id")
        valid_id = identity[0] == "movie"
        hits.append(MovieSearchHit(
            point_id=str(point.id),
            movie_id=raw_id if valid_id else None,
            imdb_id=payload.get("imdb_id"),
            tmdb_id=payload.get("tmdb_id"),
            title=payload.get("title"),
            score=score,
            id_status="present_unverified" if valid_id else "missing" if raw_id is None else "invalid",
        ))
    return MovieSearchResponse(collection=settings.qdrant_collection, mode=request.mode, hits=hits)


def _identity(point):
    payload = point.payload or {}
    movie_id = payload.get("movie_id")
    if type(movie_id) is int and 0 < movie_id <= 2**63 - 1:
        return ("movie", movie_id)
    if payload.get("imdb_id"):
        return ("imdb", payload["imdb_id"])
    return ("point", str(point.id))


def _fuse_rrf(results, limit):
    """Fuse ranks, counting each movie at most once per retrieval branch."""
    fused = {}
    for mode in ("dense", "sparse"):
        seen = set()
        for rank, point in enumerate(results.get(mode, []), start=1):
            identity = _identity(point)
            if identity in seen:
                continue
            seen.add(identity)
            contribution = 1 / (RRF_K + rank)
            representative = (rank, 0 if mode == "dense" else 1, str(point.id))
            if identity in fused:
                score, best, chosen = fused[identity]
                fused[identity] = (
                    score + contribution,
                    min(best, representative),
                    point if representative < best else chosen,
                )
            else:
                fused[identity] = (contribution, representative, point)
    ordered = sorted(fused.values(), key=lambda item: (-item[0], item[1]))
    return [(point, score) for score, _, point in ordered[:limit]]
