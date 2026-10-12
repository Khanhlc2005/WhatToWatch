from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.rag import MovieContext, RAGAnswer
from app.schemas.retrieval import MovieFilters
from app.services.chat_filters import ExtractedChatFilters


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)
    movie_ids: list[int] = Field(default_factory=list, max_length=5)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=10)
    summary: str | None = Field(default=None, max_length=1600)
    movie_context: list[MovieContext] | None = Field(default=None, max_length=20)
    filters: MovieFilters = Field(default_factory=MovieFilters)
    # Kept for old callers. The grounded baseline always uses its own prompt.
    system_prompt: str | None = None


class ChatFilterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    filters: MovieFilters = Field(default_factory=MovieFilters)


class ChatResponse(RAGAnswer):
    reply: str
    applied_filters: ExtractedChatFilters = Field(default_factory=ExtractedChatFilters)
    tool_name: str | None = None
