"""Knowledge service — deterministic knowledge base operations.

Provides list, get, search, categories, sections, and chunk operations
for telecom knowledge documents. NO Gemini, NO embeddings, NO vector search.
"""

import re
from typing import Any

from src.retrieval.knowledge_loader import (
    discover_documents,
    get_document_by_id,
    get_categories,
    parse_document,
)
from src.retrieval.chunker import chunk_documents


_documents: list[dict[str, Any]] | None = None
_chunks: list[dict[str, Any]] | None = None


def _load() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Lazy-load documents and chunks."""
    global _documents, _chunks
    if _documents is None:
        _documents = discover_documents()
        _chunks = chunk_documents(_documents)
    return _documents, _chunks


def reload_knowledge() -> int:
    """Force reload of all knowledge documents. Returns document count."""
    global _documents, _chunks
    _documents = discover_documents()
    _chunks = chunk_documents(_documents)
    return len(_documents)


def list_documents(category: str | None = None) -> list[dict[str, Any]]:
    """List all documents, optionally filtered by category."""
    docs, _ = _load()
    results = []
    for doc in docs:
        if category and doc["category"] != category:
            continue
        results.append({
            "id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "tags": doc["tags"],
            "path": doc["path"],
            "sections_count": len(doc.get("sections", [])),
        })
    return results


def get_document(document_id: str) -> dict[str, Any] | None:
    """Get a single document with full content and parsed sections."""
    doc = get_document_by_id(document_id)
    if doc is None:
        return None
    return {
        "id": doc["id"],
        "title": doc["title"],
        "category": doc["category"],
        "tags": doc["tags"],
        "path": doc["path"],
        "content": doc["content"],
        "sections": doc["sections"],
    }


def list_categories() -> list[dict[str, Any]]:
    """List all categories with document counts."""
    return get_categories()


def get_sections(document_id: str) -> list[dict[str, str]] | None:
    """Get parsed sections for a document."""
    doc = get_document_by_id(document_id)
    if doc is None:
        return None
    return doc["sections"]


def get_chunks(document_id: str) -> list[dict[str, Any]]:
    """Get all chunks for a specific document."""
    _, chunks = _load()
    return [c for c in chunks if c["document_id"] == document_id]


def search_documents(query: str, category: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Simple lexical search across documents.

    Searches in title, category, tags, section headings, and content.
    Returns matching documents ranked by relevance.
    """
    _, chunks = _load()

    query_lower = query.lower().strip()
    if not query_lower:
        return []

    query_terms = re.findall(r"\w+", query_lower)

    scored: dict[str, dict[str, Any]] = {}

    for chunk in chunks:
        if category and chunk["category"] != category:
            continue

        doc_id = chunk["document_id"]
        content_lower = chunk["content"].lower()
        heading_lower = chunk["section_heading"].lower()
        title_lower = chunk["document_title"].lower()
        cat_lower = chunk["category"].lower()

        score = 0
        for term in query_terms:
            if term in title_lower:
                score += 10
            if term in cat_lower:
                score += 5
            if term in heading_lower:
                score += 8
            if term in content_lower:
                score += 1

        if score == 0:
            continue

        if doc_id not in scored:
            scored[doc_id] = {
                "id": doc_id,
                "title": chunk["document_title"],
                "category": chunk["category"],
                "score": 0,
                "matching_chunks": [],
                "preview": "",
            }

        scored[doc_id]["score"] += score
        if len(scored[doc_id]["matching_chunks"]) < 3:
            preview = chunk["content"][:200]
            if len(chunk["content"]) > 200:
                preview += "..."
            scored[doc_id]["matching_chunks"].append({
                "chunk_id": chunk["chunk_id"],
                "section_heading": chunk["section_heading"],
                "preview": preview,
                "score": score,
            })

    results = sorted(scored.values(), key=lambda x: x["score"], reverse=True)[:limit]

    for r in results:
        if r["matching_chunks"]:
            r["preview"] = r["matching_chunks"][0]["preview"]

    return results


def route_ticket_to_categories(ticket_category: str) -> list[str]:
    """Map a ticket category to relevant knowledge base categories."""
    mapping: dict[str, list[str]] = {
        "connectivity": ["connectivity", "network"],
        "data": ["connectivity", "billing"],
        "billing": ["billing"],
        "device": ["device"],
        "roaming": ["roaming"],
        "network": ["network"],
        "coverage": ["network", "connectivity"],
        "voice": ["connectivity", "network"],
        "sms": ["connectivity"],
        "mms": ["connectivity"],
        "account": ["support"],
        "security": ["support"],
        "complaint": ["support", "escalation"],
        "enterprise": ["enterprise"],
    }
    key = ticket_category.lower().strip()
    return mapping.get(key, ["support"])
