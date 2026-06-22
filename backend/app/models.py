from pydantic import BaseModel


class IngestRequest(BaseModel):
    url: str
    domain: str
    title: str
    content: str


class IngestResponse(BaseModel):
    status: str
    chunks_stored: int
    url: str


class ChatRequest(BaseModel):
    url: str
    domain: str
    question: str
    mode: str = "page"  # "page" or "website"
    chat_history: list[dict[str, str]] = []


class SourceCitation(BaseModel):
    title: str
    url: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceCitation] = []
