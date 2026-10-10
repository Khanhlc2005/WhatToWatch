import logging

from fastapi import APIRouter, HTTPException

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation import recommend_movies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/recommendations", tags=["Recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        return recommend_movies(request)
    except Exception as exc:
        logger.exception("Recommendation retrieval failed")
        raise HTTPException(status_code=503, detail="Recommendation retrieval is unavailable") from exc
