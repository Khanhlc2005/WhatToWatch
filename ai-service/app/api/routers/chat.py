import logging

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from requests import RequestException

from app.llm_client import OllamaClient
from app.schemas.chat import ChatFilterRequest, ChatRequest, ChatResponse
from app.schemas.rag import RAGAnswer
from app.schemas.retrieval import MovieSearchRequest
from app.services.chat_filters import ExtractedChatFilters, extract_chat_filters
from app.services.chat_tools import (
    answer_with_comparison_tool,
    answer_with_detail_tool,
    is_comparison,
    is_detail,
)
from app.services.context_builder import (
    MAX_CONTEXT_MOVIES,
    MAX_RETRIEVAL_CANDIDATES,
    MovieCatalogUnavailable,
    build_context_for_movie_ids,
    build_movie_context,
)
from app.services.rag import (
    RAGFormatError,
    RAGGroundingError,
    RAGInputError,
    answer_question,
)
from app.services.retrieval import search_movies

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/internal/chat",
    tags=["Chatbot"],
)


def _follow_up_movie_ids(request: ChatRequest) -> list[int]:
    question = request.message.casefold()
    references = ("phim đó", "phim này", "bộ phim đó", "bộ phim này", "phim ấy", "the movie", "that film", "this film")
    if not any(reference in question for reference in references):
        return []
    for turn in reversed(request.history):
        if turn.role == "assistant" and turn.movie_ids:
            return turn.movie_ids[:MAX_CONTEXT_MOVIES]
    return []


def _validated_filters(message: str, filters) -> ExtractedChatFilters:
    try:
        return extract_chat_filters(message, filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid filters in the question") from exc


@router.post("/filters", response_model=ExtractedChatFilters)
def chat_filters(request: ChatFilterRequest) -> ExtractedChatFilters:
    """Inspect validated natural-language filters without calling retrieval or Ollama."""
    return _validated_filters(request.message, request.filters)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Retrieve real movies, hydrate them from MySQL, then generate a grounded answer."""
    extracted = _validated_filters(request.message, request.filters)
    context = request.movie_context
    if context is None:
        prior_ids = _follow_up_movie_ids(request)
        try:
            search = search_movies(MovieSearchRequest(
                query=request.message, mode="hybrid",
                rerank=True, candidate_k=20,
                limit=MAX_RETRIEVAL_CANDIDATES, filters=extracted.retrieval,
            ))
        except Exception as exc:
            logger.exception("Chat retrieval failed")
            raise HTTPException(status_code=503, detail="Movie retrieval is unavailable") from exc
        try:
            context = build_movie_context(search, director=extracted.director, actor=extracted.actor)
            if prior_ids:
                prior_context = build_context_for_movie_ids(prior_ids)
                retrieved_by_id = {movie.movie_id: movie for movie in context}
                prior_context = [
                    movie.model_copy(update={"genres": retrieved_by_id[movie.movie_id].genres})
                    if movie.movie_id in retrieved_by_id else movie
                    for movie in prior_context
                ]
                seen = {movie.movie_id for movie in prior_context}
                context = (prior_context + [movie for movie in context if movie.movie_id not in seen])[:MAX_CONTEXT_MOVIES]
        except MovieCatalogUnavailable as exc:
            logger.exception("Chat catalog lookup failed")
            raise HTTPException(status_code=503, detail="Movie catalog is unavailable") from exc

    try:
        tool_name = None
        if request.movie_context is None and not search.hits and not context:
            result = RAGAnswer(
                status="no_match", answer="No matching movies were found in the available data.", movies=[],
            )
        elif is_comparison(request.message):
            result = answer_with_comparison_tool(request.message, context, request.history)
            tool_name = "compare_movies"
        elif is_detail(request.message):
            result = answer_with_detail_tool(request.message, context, request.history)
            tool_name = "movie_detail"
        else:
            result = answer_question(
                request.message,
                context,
                lambda prompt, system: OllamaClient().generate(
                    prompt,
                    system_prompt=system,
                    response_format=RAGAnswer.model_json_schema(),
                ),
                history=request.history,
                summary=request.summary,
            )
    except MovieCatalogUnavailable as exc:
        raise HTTPException(status_code=503, detail="Movie catalog is unavailable") from exc
    except RAGInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (RAGFormatError, RAGGroundingError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama is unavailable") from exc

    details = "\n".join(f"- {movie.title}: {movie.reason}" for movie in result.movies)
    reply = result.answer + ("\n" + details if details else "")
    return ChatResponse(**result.model_dump(), reply=reply,
                        applied_filters=extracted, tool_name=tool_name)
