from pydantic import BaseModel


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
