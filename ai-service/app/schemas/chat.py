from pydantic import BaseModel, ConfigDict, Field

from app.schemas.rag import MovieContext, RAGAnswer


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    movie_context: list[MovieContext] | None = Field(default=None, max_length=20)
    # Kept for old callers. The grounded baseline always uses its own prompt.
    system_prompt: str | None = None


class ChatResponse(RAGAnswer):
    reply: str
