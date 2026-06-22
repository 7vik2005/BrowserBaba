from fastapi import APIRouter
from app.models import ChatRequest, ChatResponse
from app.rag import run_rag

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = run_rag(
        question=request.question,
        url=request.url,
        domain=request.domain,
        mode=request.mode,
        chat_history=request.chat_history,
    )
    return ChatResponse(answer=result["answer"], sources=result["sources"])
