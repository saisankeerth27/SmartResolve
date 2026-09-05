"""Embedder — wraps Gemini embedding API for knowledge chunks.

Provides deterministic metadata association and handles API errors.
"""

import logging
import time
from typing import Any

from src.ai.gemini_client import embed_text, embed_texts, is_available
from src.core.config import GEMINI_EMBEDDING_MODEL as EMBEDDING_MODEL

logger = logging.getLogger(__name__)
EMBEDDING_TASK_DOCUMENT = "RETRIEVAL_DOCUMENT"
EMBEDDING_TASK_QUERY = "RETRIEVAL_QUERY"


def embed_query(text: str) -> list[float] | None:
    """Embed a search query text."""
    if not is_available():
        return None
    return embed_text(text, task_type=EMBEDDING_TASK_QUERY)


def embed_chunks(chunks: list[dict[str, Any]], batch_size: int = 100) -> list[list[float]] | None:
    """Embed a list of knowledge chunks in batches.

    Each chunk must have a 'content' key.
    Returns list of embeddings in same order as input chunks, or None on failure.
    """
    if not is_available():
        return None

    all_embeddings: list[list[float]] = []
    max_retries = 3

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]

        for attempt in range(max_retries):
            result = embed_texts(texts, task_type=EMBEDDING_TASK_DOCUMENT)
            if result is not None:
                all_embeddings.extend(result)
                logger.info("Embedded batch %d/%d (%d chunks)",
                             i // batch_size + 1,
                             (len(chunks) + batch_size - 1) // batch_size,
                             len(batch))
                break
            else:
                wait = 60 * (attempt + 1)
                logger.warning("Embedding batch failed, retry %d/%d in %ds",
                               attempt + 1, max_retries, wait)
                time.sleep(wait)
        else:
            logger.error("Failed to embed batch starting at index %d after %d retries", i, max_retries)
            return None

    return all_embeddings


def get_embedding_dimension() -> int | None:
    """Get the embedding dimension by embedding a test text."""
    if not is_available():
        return None
    test = embed_text("test dimension", task_type=EMBEDDING_TASK_QUERY)
    if test:
        return len(test)
    return None
