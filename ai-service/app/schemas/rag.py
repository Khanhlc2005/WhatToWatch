"""Contract shared by the baseline chatbot and a future retrieval adapter."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MovieContext(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    movie_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    year: int | None = Field(default=None, ge=1888, le=2100)
    genres: list[str] = Field(default_factory=list)
    overview: str | None = Field(default=None, min_length=1)
    director: str | None = None
    runtime_minutes: int | None = Field(default=None, gt=0)


class AnswerMovie(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    movie_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class RAGAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["answered", "no_match", "insufficient_context"]
    answer: str = Field(min_length=12)
    movies: list[AnswerMovie] = Field(max_length=5)

    @model_validator(mode="after")
    def status_matches_movies(self) -> "RAGAnswer":
        if self.status == "answered" and not self.movies:
            raise ValueError("answered requires at least one movie")
        if self.status != "answered" and self.movies:
            raise ValueError("fallback answers cannot recommend movies")
        return self
