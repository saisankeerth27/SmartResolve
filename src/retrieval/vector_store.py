"""Local FAISS vector store for knowledge embeddings.

Stores index at index/knowledge.faiss with metadata at index/metadata.json.
Runs entirely locally — no hosted vector databases.
"""

import json
import logging
from pathlib import Path
from typing import Any

import faiss
import numpy as np

logger = logging.getLogger(__name__)

INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "index"
FAISS_PATH = INDEX_DIR / "knowledge.faiss"
METADATA_PATH = INDEX_DIR / "metadata.json"
INDEX_META_PATH = INDEX_DIR / "index_meta.json"


class VectorStore:
    """Local FAISS-based vector store."""

    def __init__(self):
        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[dict[str, Any]] = []
        self._index_meta: dict[str, Any] = {}
        self._loaded = False

    def load(self) -> bool:
        """Load FAISS index and metadata from disk."""
        if self._loaded:
            return True

        if not FAISS_PATH.exists() or not METADATA_PATH.exists():
            logger.warning("FAISS index not found at %s", FAISS_PATH)
            return False

        try:
            self._index = faiss.read_index(str(FAISS_PATH))

            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            if INDEX_META_PATH.exists():
                with open(INDEX_META_PATH, "r", encoding="utf-8") as f:
                    self._index_meta = json.load(f)

            if self._index.ntotal != len(self._metadata):
                logger.error("FAISS index/metadata mismatch: %d vectors vs %d metadata entries",
                             self._index.ntotal, len(self._metadata))
                return False

            self._loaded = True
            logger.info("Loaded FAISS index: %d vectors, dimension %d",
                        self._index.ntotal, self._index.d)
            return True
        except Exception as e:
            logger.error("Failed to load FAISS index: %s", e)
            return False

    def is_loaded(self) -> bool:
        return self._loaded and self._index is not None

    @property
    def dimension(self) -> int | None:
        if self._index:
            return self._index.d
        return None

    @property
    def total_vectors(self) -> int:
        if self._index:
            return self._index.ntotal
        return 0

    @property
    def index_meta(self) -> dict[str, Any]:
        return self._index_meta

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """Search the index for the most similar vectors.

        Returns list of dicts with chunk metadata and similarity score.
        """
        if not self.is_loaded():
            return []

        try:
            query_vec = np.array([query_embedding], dtype=np.float32)
            scores, indices = self._index.search(query_vec, min(top_k, self._index.ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._metadata):
                    continue
                meta = self._metadata[idx].copy()
                meta["score"] = float(score)
                results.append(meta)

            return results
        except Exception as e:
            logger.error("FAISS search failed: %s", e)
            return []

    def save(self, index: faiss.IndexFlatIP, metadata: list[dict[str, Any]],
             meta_info: dict[str, Any]) -> None:
        """Save index and metadata to disk."""
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(FAISS_PATH))
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        with open(INDEX_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta_info, f, indent=2, ensure_ascii=False)
        logger.info("Saved FAISS index to %s", FAISS_PATH)


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
        _store.load()
    return _store
