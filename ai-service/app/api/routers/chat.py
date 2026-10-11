import logging

from fastapi import APIRouter, HTTPException
from requests import RequestException

from app.llm_client import OllamaClient
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.rag import RAGAnswer
from app.schemas.retrieval import MovieSearchRequest
from app.services.context_builder import (
    MAX_RETRIEVAL_CANDIDATES,
    MovieCatalogUnavailable,
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


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Retrieve real movies, hydrate them from MySQL, then generate a grounded answer."""
    context = request.movie_context
    if context is None:
        try:
            search = search_movies(MovieSearchRequest(
                query=request.message, mode="hybrid",
                limit=MAX_RETRIEVAL_CANDIDATES, filters=request.filters,
            ))
        except Exception as exc:
            logger.exception("Chat retrieval failed")
            raise HTTPException(status_code=503, detail="Movie retrieval is unavailable") from exc
        try:
            context = build_movie_context(search)
        except MovieCatalogUnavailable as exc:
            logger.exception("Chat catalog lookup failed")
            raise HTTPException(status_code=503, detail="Movie catalog is unavailable") from exc

    try:
        if request.movie_context is None and not search.hits:
            result = RAGAnswer(
                status="no_match", answer="Không tìm thấy phim phù hợp trong dữ liệu hiện có.", movies=[],
            )
        else:
            result = answer_question(
                request.message,
                context,
                lambda prompt, system: OllamaClient().generate(
                    prompt,
                    system_prompt=system,
                    response_format=RAGAnswer.model_json_schema(),
                ),
            )
    except RAGInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (RAGFormatError, RAGGroundingError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RequestException as exc:
        raise HTTPException(status_code=503, detail="Ollama không khả dụng") from exc

    details = "\n".join(f"- {movie.title}: {movie.reason}" for movie in result.movies)
    reply = result.answer + ("\n" + details if details else "")
    return ChatResponse(**result.model_dump(), reply=reply)
