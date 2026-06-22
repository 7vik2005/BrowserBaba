import re
from fastapi import APIRouter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models import IngestRequest, IngestResponse
from app.config import get_settings
from app.vectorstore import add_documents, delete_by_url

router = APIRouter()
settings = get_settings()


def clean_text(text: str) -> str:
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace tabs/multiple spaces with a single space, preserving newlines
    text = re.sub(r"[^\S\n]+", " ", text)
    # Limit consecutive newlines to maximum of 2 (paragraph blocks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing spaces for each line
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_page(request: IngestRequest):
    cleaned = clean_text(request.content)

    if len(cleaned) < 50:
        return IngestResponse(status="skipped", chunks_stored=0, url=request.url)

    delete_by_url(request.url)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(cleaned)

    stored = add_documents(chunks, request.url, request.title, request.domain)

    return IngestResponse(status="ok", chunks_stored=stored, url=request.url)
