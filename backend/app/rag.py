from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.vectorstore import search
from app.prompts import RAG_PROMPT
from app.llm_factory import get_llm

import logging

logger = logging.getLogger(__name__)
settings = get_settings()

prompt = ChatPromptTemplate.from_template(RAG_PROMPT)


def rerank_chunks(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """
    Reranks chunks by combining the vector similarity score with a 
    keyword-overlap frequency weight to enhance exact match retrieval.
    """
    if not chunks:
        return []

    query_words = set(query.lower().split())

    reranked = []
    for chunk in chunks:
        text = chunk.get("text", "").lower()
        # Calculate matching keywords count
        overlap = sum(1 for word in query_words if word in text)

        # Keyword density metric to prevent favoring long chunks
        words = text.split()
        density = (overlap / len(words)) if words else 0.0

        # Combine vector cosine score and keyword density weight
        combined_score = chunk["score"] + (density * 1.5)

        chunk_copy = chunk.copy()
        chunk_copy["combined_score"] = combined_score
        reranked.append(chunk_copy)

    # Sort descending by the combined similarity metrics
    reranked.sort(key=lambda x: x["combined_score"], reverse=True)
    return reranked[:top_k]


def _build_fallback_answer(results: list[dict]) -> str:
    """
    Returns a structured fallback message when the LLM quota is exhausted.
    """
    context_chunks = []
    for result in results[:3]:
        text = result.get("text", "").strip()
        if text:
            context_chunks.append(text)

    fallback_context = "\n\n---\n\n".join(context_chunks)

    return (
        "⚠️ LLM API quota exceeded.\n\n"
        "The query was successfully matched against the local knowledge base.\n\n"
        "Retrieved Context:\n\n"
        f"{fallback_context}"
    )


def _invoke_chain_with_fallback(inputs: dict, results: list[dict]) -> str:
    try:
        # Dynamically instantiate the model from our LLM factory
        llm = get_llm()
        chain = prompt | llm | StrOutputParser()
        return chain.invoke(inputs)

    except Exception as e:
        error_text = str(e).lower()
        quota_indicators = [
            "429",
            "quota",
            "resource exhausted",
            "resource_exhausted",
            "rate limit",
            "generaterequestsperminute",
            "generaterequestsperday",
        ]

        if any(indicator in error_text for indicator in quota_indicators):
            logger.warning("LLM quota exceeded. Returning fallback answer.")
            return _build_fallback_answer(results)

        logger.exception("RAG Generation Error")
        return f"Error generating response: {str(e)}"


def run_rag(
    question: str,
    url: str,
    domain: str = None,
    mode: str = "page",
    chat_history: list[dict] = None,
) -> dict:
    # 1. Fetch top 10 chunks from vector database
    results = search(
        query=question,
        url=url,
        domain=domain,
        mode=mode,
        top_k=10
    )

    if not results:
        return {
            "answer": (
                "I don't have any information about this page yet. "
                "Try scanning the page first."
            ),
            "sources": [],
        }

    # 2. Apply lexical reranking to filter down to top 3 chunks
    top_chunks = rerank_chunks(question, results, top_k=3)

    # 3. Format inputs for prompting
    context = "\n\n---\n\n".join(
        [chunk["text"] for chunk in top_chunks]
    )

    history_str = ""
    if chat_history:
        for msg in chat_history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"{role}: {content}\n"

    inputs = {
        "context": context,
        "question": question,
        "chat_history": history_str if history_str else "None",
    }

    # 4. Execute prompt generation
    answer = _invoke_chain_with_fallback(
        inputs=inputs,
        results=top_chunks,
    )

    # 5. Extract sources for citations
    sources = []
    seen_urls = set()
    for chunk in top_chunks:
        url_val = chunk["url"]
        if url_val not in seen_urls:
            seen_urls.add(url_val)
            sources.append({
                "title": chunk.get("title", "Untitled Page"),
                "url": url_val,
                "score": round(chunk.get("score", 0.0), 3)
            })

    return {
        "answer": answer,
        "sources": sources,
    }
