from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class SampleMoviePoint(BaseModel):
    id: str
    title: str | None = None
    imdb_id: str | None = None
    year: int | None = None


class SampleRetrievalResponse(BaseModel):
    collection: str
    count: int
    points: list[SampleMoviePoint]


class QdrantHealthResponse(BaseModel):
    url: str
    collections: list[str]
    target_collection: str
    target_collection_exists: bool


FilterValue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class MovieFilters(BaseModel):
    """Only fields written by index_sample_movies.make_payload are supported.

    List filters match any requested value; separate fields are ANDed.
    Vocabulary is not invented: unknown values simply match no points.
    """

    model_config = ConfigDict(extra="forbid")
    genres: list[FilterValue] = Field(default_factory=list, max_length=50)
    exclude_genres: list[FilterValue] = Field(default_factory=list, max_length=50)
    languages: list[FilterValue] = Field(default_factory=list, max_length=50)
    countries: list[FilterValue] = Field(default_factory=list, max_length=50)
    year_min: int | None = Field(default=None, ge=1, le=9999, strict=True)
    year_max: int | None = Field(default=None, ge=1, le=9999, strict=True)
    rating_min: float | None = Field(default=None, ge=0, le=10, allow_inf_nan=False)
    runtime_max: int | None = Field(default=None, ge=1, strict=True)

    @model_validator(mode="after")
    def ordered_years(self):
        if self.year_min is not None and self.year_max is not None and self.year_min > self.year_max:
            raise ValueError("year_min must not exceed year_max")
        return self


class MovieSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    mode: Literal["dense", "sparse"] = "dense"
    limit: int = Field(default=10, ge=1, le=100, strict=True)
    filters: MovieFilters = Field(default_factory=MovieFilters)


class MovieSearchHit(BaseModel):
    point_id: str
    movie_id: int | None
    imdb_id: str | None
    tmdb_id: int | None
    title: str | None
    score: float
    # Presence is not proof that the ID exists in MySQL; the offline audit proves that.
    id_status: Literal["present_unverified", "missing", "invalid"]


class MovieSearchResponse(BaseModel):
    collection: str
    mode: Literal["dense", "sparse"]
    hits: list[MovieSearchHit]
