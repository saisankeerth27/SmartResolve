"""Deterministic section-based chunker for knowledge documents.

Each chunk is traceable to a document, section, and chunk index for citation.
Chunks are 300–700 words with section heading context included.
"""

import re
from typing import Any


TARGET_MIN_WORDS = 300
TARGET_MAX_WORDS = 700


def _word_count(text: str) -> int:
    """Count words in a text block."""
    return len(re.findall(r"\S+", text))


def _split_paragraphs(text: str) -> list[str]:
    """Split text into non-empty paragraph blocks."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_section(
    section_heading: str,
    section_content: str,
    document_id: str,
    document_title: str,
    category: str,
    start_index: int = 0,
) -> list[dict[str, Any]]:
    """Chunk a single section into word-count-bounded pieces.

    Returns a list of chunk dicts with citation-friendly IDs.
    """
    if not section_content.strip():
        return []

    paragraphs = _split_paragraphs(section_content)
    if not paragraphs:
        return []

    chunks: list[dict[str, Any]] = []
    current_paras: list[str] = []
    current_words = 0
    chunk_idx = start_index

    for para in paragraphs:
        para_words = _word_count(para)

        if current_words + para_words > TARGET_MAX_WORDS and current_paras:
            chunk_text = "\n\n".join(current_paras)
            chunks.append({
                "chunk_id": f"{document_id}::s{chunk_idx}",
                "document_id": document_id,
                "document_title": document_title,
                "category": category,
                "section_heading": section_heading,
                "chunk_index": chunk_idx,
                "content": chunk_text,
                "word_count": current_words,
            })
            chunk_idx += 1
            current_paras = []
            current_words = 0

        current_paras.append(para)
        current_words += para_words

    if current_paras:
        chunk_text = "\n\n".join(current_paras)
        chunks.append({
            "chunk_id": f"{document_id}::s{chunk_idx}",
            "document_id": document_id,
            "document_title": document_title,
            "category": category,
            "section_heading": section_heading,
            "chunk_index": chunk_idx,
            "content": chunk_text,
            "word_count": current_words,
        })

    return chunks


def chunk_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Chunk an entire document into citation-friendly pieces.

    The document dict must have: id, title, category, sections (list of heading+content).
    """
    all_chunks: list[dict[str, Any]] = []
    global_idx = 0

    for section in document.get("sections", []):
        heading = section.get("heading", "")
        content = section.get("content", "")
        chunks = chunk_section(
            section_heading=heading,
            section_content=content,
            document_id=document["id"],
            document_title=document["title"],
            category=document["category"],
            start_index=global_idx,
        )
        all_chunks.extend(chunks)
        global_idx += len(chunks)

    return all_chunks


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chunk multiple documents and return all chunks."""
    all_chunks: list[dict[str, Any]] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))
    return all_chunks
