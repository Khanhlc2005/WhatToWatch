from fastapi import APIRouter, HTTPException

from app.llm_client import OllamaClient
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/internal/chat",
    tags=["Chatbot"],
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Điểm tích hợp thống nhất với module chatbot/RAG của Nam Anh."""
    try:
        client = OllamaClient()
        reply = client.generate(request.message, system_prompt=request.system_prompt)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Chatbot không khả dụng: {exc}") from exc

    return ChatResponse(reply=reply)
