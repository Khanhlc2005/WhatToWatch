from fastapi import APIRouter, HTTPException
from requests import RequestException

from app.llm_client import OllamaClient
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.rag import RAGAnswer
from app.services.rag import (
    RAGFormatError,
    RAGGroundingError,
    RAGInputError,
    answer_question,
    load_sample_context,
)

router = APIRouter(
    prefix="/internal/chat",
    tags=["Chatbot"],
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Grounded baseline; omitted context uses the checked-in movie fixture."""
    context = request.movie_context
    if context is None:
        context = load_sample_context()
    try:
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
