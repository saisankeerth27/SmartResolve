"""Deterministic knowledge document loader — discovers, reads, and parses Markdown documents."""

import json
import re
from pathlib import Path
from typing import Any


KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"
MANIFEST_PATH = KNOWLEDGE_DIR / "manifest.json"


def load_manifest() -> dict[str, Any]:
    """Load and return the knowledge manifest."""
    if not MANIFEST_PATH.exists():
        return {"version": "1.0", "documents": []}
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def discover_documents() -> list[dict[str, Any]]:
    """Discover all documents listed in the manifest with metadata."""
    manifest = load_manifest()
    documents = []
    for doc_meta in manifest.get("documents", []):
        doc_path = KNOWLEDGE_DIR / doc_meta["path"]
        if not doc_path.exists():
            continue
        content = doc_path.read_text(encoding="utf-8")
        documents.append({
            "id": doc_meta["id"],
            "title": doc_meta["title"],
            "category": doc_meta["category"],
            "tags": doc_meta.get("tags", []),
            "path": doc_meta["path"],
            "content": content,
            "sections": parse_document(content),
        })
    return documents


def parse_document(content: str) -> list[dict[str, str]]:
    """Parse Markdown content into sections based on ## headings.

    Returns a list of dicts with 'heading' and 'content' keys.
    The first section may have an empty heading if content precedes the first ##.
    """
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []

    for line in content.split("\n"):
        if re.match(r"^##\s+", line):
            if current_lines or current_heading:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_lines).strip(),
                })
            current_heading = re.sub(r"^##\s+", "", line).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines or current_heading:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_lines).strip(),
        })

    return sections


def get_document_by_id(document_id: str) -> dict[str, Any] | None:
    """Retrieve a single document by its ID."""
    manifest = load_manifest()
    for doc_meta in manifest.get("documents", []):
        if doc_meta["id"] == document_id:
            doc_path = KNOWLEDGE_DIR / doc_meta["path"]
            if not doc_path.exists():
                return None
            content = doc_path.read_text(encoding="utf-8")
            return {
                "id": doc_meta["id"],
                "title": doc_meta["title"],
                "category": doc_meta["category"],
                "tags": doc_meta.get("tags", []),
                "path": doc_meta["path"],
                "content": content,
                "sections": parse_document(content),
            }
    return None


def get_categories() -> list[dict[str, Any]]:
    """Return all categories with document counts."""
    manifest = load_manifest()
    cat_counts: dict[str, int] = {}
    for doc in manifest.get("documents", []):
        cat = doc["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    return [{"category": c, "count": n} for c, n in sorted(cat_counts.items())]
