from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Identifier = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]


class RatingSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    movie_id: Identifier
    rating: float = Field(strict=True, ge=1, le=5, allow_inf_nan=False)


class PreferenceSnapshot(BaseModel):
    """Complete current ratings, not a page or an event delta."""

    model_config = ConfigDict(extra="forbid")
    user_id: Identifier
    ratings: list[RatingSignal] = Field(max_length=10000)

    @model_validator(mode="after")
    def unique_movies(self):
        ids = [rating.movie_id for rating in self.ratings]
        if len(ids) != len(set(ids)):
            raise ValueError("Snapshot contains duplicate movie_id")
        return self


class SkippedMovie(BaseModel):
    movie_id: int
    reason: Literal["missing_embedding", "invalid_embedding", "ambiguous_movie_id"]


class PreferenceResponse(BaseModel):
    user_id: int
    status: Literal["ready", "cold_start"]
    reason: Literal["insufficient_ratings", "zero_vector"] | None
    profile_version: str
    last_updated: str
    rating_count: int
    usable_rating_count: int
    skipped_movies: list[SkippedMovie]
