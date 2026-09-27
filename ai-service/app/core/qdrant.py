from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException

from app.core.config import settings


class QdrantConnectionError(RuntimeError):
    pass


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, timeout=10)


def check_qdrant_connection() -> dict[str, object]:
    client = get_qdrant_client()

    try:
        collections = [c.name for c in client.get_collections().collections]
    except ResponseHandlingException as exc:
        raise QdrantConnectionError(
            f"Không kết nối được Qdrant tại {settings.qdrant_url}: {exc}"
        ) from exc
    except Exception as exc:
        raise QdrantConnectionError(
            f"Lỗi không xác định khi kết nối Qdrant: {exc}"
        ) from exc

    return {
        "url": settings.qdrant_url,
        "collections": collections,
        "target_collection": settings.qdrant_collection,
        "target_collection_exists": settings.qdrant_collection in collections,
    }
