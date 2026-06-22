from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import get_settings
import uuid
import time
import logging
import re

logger = logging.getLogger(__name__)

settings = get_settings()

def get_qdrant_client():
    """Initializes Qdrant client, falling back to local on-disk storage if server is unreachable."""
    try:
        c = QdrantClient(url=settings.qdrant_url, timeout=2.0, check_compatibility=False)
        # Test connection by listing collections
        c.get_collections()
        logger.info(f"Successfully connected to Qdrant server at {settings.qdrant_url}")
        return c
    except Exception as e:
        logger.warning(
            f"Could not connect to Qdrant server at {settings.qdrant_url} (Error: {e}). "
            f"Falling back to local disk storage in './qdrant_db' directory."
        )
        return QdrantClient(path="./qdrant_db")

client = get_qdrant_client()

embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.embedding_model,
    google_api_key=settings.gemini_api_key,
)


def ensure_collection():
    target_size = 3072
    collections = [c.name for c in client.get_collections().collections]
    if settings.collection_name in collections:
        col_info = client.get_collection(settings.collection_name)
        current_size = col_info.config.params.vectors.size
        if current_size != target_size:
            client.delete_collection(settings.collection_name)
            collections.remove(settings.collection_name)

    if settings.collection_name not in collections:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(size=target_size, distance=Distance.COSINE),
        )


def _embed_documents_with_retry(chunks: list[str]) -> list[list[float]]:
    """Embeds a list of chunks in batches, handling rate limits with backoff."""
    if not chunks:
        return []

    batch_size = 15
    vectors = []

    total_chunks = len(chunks)
    num_batches = (total_chunks + batch_size - 1) // batch_size

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        batch_num = i // batch_size + 1

        retries = 0
        max_retries = 7
        backoff = 5.0  # initial backoff in seconds

        while True:
            try:
                logger.info(f"Embedding batch {batch_num}/{num_batches} ({len(batch)} chunks)...")
                batch_vectors = embeddings.embed_documents(batch)
                vectors.extend(batch_vectors)
                break
            except Exception as e:
                err_msg = str(e)
                # Check if this is a rate limit/quota error
                is_quota_error = any(
                    indicator in err_msg.lower()
                    for indicator in ["429", "rate limit", "quota", "resource exhausted", "resource_exhausted"]
                )

                if is_quota_error and retries < max_retries:
                    retries += 1
                    
                    # Try to extract the specific retry delay suggested by the API
                    wait_time = backoff
                    delay_match = re.search(r"Please retry in ([\d\.]+)s", err_msg)
                    if delay_match:
                        wait_time = float(delay_match.group(1)) + 1.0
                    else:
                        delay_match2 = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_msg)
                        if delay_match2:
                            wait_time = float(delay_match2.group(1)) + 1.0

                    logger.warning(
                        f"Rate limit hit embedding batch {batch_num}/{num_batches}. "
                        f"Retrying in {wait_time:.2f}s (attempt {retries}/{max_retries}). Error: {err_msg}"
                    )
                    time.sleep(wait_time)
                    backoff = max(backoff * 2.0, wait_time * 1.5)  # increase backoff dynamically
                else:
                    logger.error(f"Failed to embed batch {batch_num}/{num_batches}: {e}")
                    raise e

        # Add a small delay between batches to avoid hitting rate limits immediately
        if i + batch_size < total_chunks:
            time.sleep(1.0)

    return vectors


def add_documents(chunks: list[str], url: str, title: str, domain: str) -> int:
    ensure_collection()

    vectors = _embed_documents_with_retry(chunks)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": chunk, "url": url, "title": title, "domain": domain},
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    client.upsert(collection_name=settings.collection_name, points=points)
    return len(points)


def search(query: str, url: str, domain: str = None, mode: str = "page", top_k: int = None) -> list[dict]:
    ensure_collection()

    if top_k is None:
        top_k = settings.top_k

    query_vector = embeddings.embed_query(query)

    # Filter based on search mode (page-specific vs website-wide domain)
    if mode == "website" and domain:
        search_filter = Filter(
            must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
        )
    else:
        search_filter = Filter(
            must=[FieldCondition(key="url", match=MatchValue(value=url))]
        )

    results = client.query_points(
        collection_name=settings.collection_name,
        query=query_vector,
        query_filter=search_filter,
        limit=top_k,
    )

    return [
        {
            "text": point.payload["text"],
            "url": point.payload["url"],
            "title": point.payload.get("title", "Untitled Page"),
            "domain": point.payload.get("domain", ""),
            "score": point.score,
        }
        for point in results.points
    ]


def delete_by_url(url: str):
    ensure_collection()
    client.delete(
        collection_name=settings.collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="url", match=MatchValue(value=url))]
        ),
    )
