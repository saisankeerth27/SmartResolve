"""Retriever — retrieves relevant knowledge chunks using FAISS + Gemini embeddings.

Supports category filtering, relevance threshold, and duplicate reduction.
"""

import logging
from typing import Any

from src.retrieval.embedder import embed_query
from src.retrieval.vector_store import get_vector_store

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
RELEVANCE_THRESHOLD = 0.25


def retrieve_relevant_chunks(
    query: str,
    candidate_categories: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = RELEVANCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Retrieve relevant knowledge chunks for a query.

    Args:
        query: The search query text.
        candidate_categories: Optional list of categories to prefer.
        top_k: Number of results to return.
        threshold: Minimum similarity score to include.

    Returns:
        List of chunk dicts with metadata and score.
    """
    store = get_vector_store()
    if not store.is_loaded():
        logger.warning("FAISS index not loaded — retrieval unavailable")
        return []

    query_embedding = embed_query(query)
    if query_embedding is None:
        logger.error("Failed to embed query — retrieval unavailable")
        return []

    search_k = top_k * 3 if candidate_categories else top_k * 2
    search_k = min(search_k, store.total_vectors)

    raw_results = store.search(query_embedding, top_k=search_k)

    filtered = []
    for r in raw_results:
        if r["score"] < threshold:
            continue
        if candidate_categories and r.get("category") not in candidate_categories:
            r["score"] *= 0.5
        filtered.append(r)

    deduplicated = _deduplicate_results(filtered, top_k)

    return deduplicated[:top_k]


def _deduplicate_results(results: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Reduce duplicate chunks from the same document, preferring diversity."""
    seen_docs: dict[str, int] = {}
    deduplicated: list[dict[str, Any]] = []

    for r in results:
        doc_id = r.get("document_id", "")
        count = seen_docs.get(doc_id, 0)
        if count >= 2:
            continue
        seen_docs[doc_id] = count + 1
        deduplicated.append(r)
        if len(deduplicated) >= limit:
            break

    return deduplicated
