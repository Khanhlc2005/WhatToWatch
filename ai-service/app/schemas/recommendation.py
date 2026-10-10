from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.preference import Identifier
from app.schemas.retrieval import MovieFilters


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: Identifier
    limit: int = Field(default=10, strict=True, ge=1, le=100)
    filters: MovieFilters = Field(default_factory=MovieFilters)
    exclude_movie_ids: list[Identifier] = Field(default_factory=list, max_length=10000)


class RecommendationHit(BaseModel):
    movie_id: Identifier
    score: float = Field(allow_inf_nan=False)


class RecommendationResponse(BaseModel):
    user_id: int
    status: Literal["ready", "cold_start"]
    hits: list[RecommendationHit]
