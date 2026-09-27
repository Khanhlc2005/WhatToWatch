from fastapi import APIRouter, HTTPException

from app.core.qdrant import QdrantConnectionError, check_qdrant_connection
from app.schemas.retrieval import QdrantHealthResponse, SampleRetrievalResponse
from app.services.retrieval import fetch_sample_movies

router = APIRouter(
    prefix="/internal/qdrant",
    tags=["Qdrant"],
)


@router.get("/health", response_model=QdrantHealthResponse)
def qdrant_health() -> QdrantHealthResponse:
    try:
        status = check_qdrant_connection()
    except QdrantConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return QdrantHealthResponse(**status)


@router.get("/sample", response_model=SampleRetrievalResponse)
def qdrant_sample(limit: int = 5) -> SampleRetrievalResponse:
    try:
        return fetch_sample_movies(limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Không truy xuất được dữ liệu mẫu từ Qdrant: {exc}",
        ) from exc
