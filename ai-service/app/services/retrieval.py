from app.core.config import settings
from app.core.qdrant import get_qdrant_client
from app.schemas.retrieval import SampleMoviePoint, SampleRetrievalResponse


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
