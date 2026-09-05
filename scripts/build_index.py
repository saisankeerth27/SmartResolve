"""Build FAISS index from knowledge documents.

Usage:
    python scripts/build_index.py

This script:
1. Loads knowledge documents from the manifest.
2. Validates documents.
3. Generates chunks.
4. Generates embeddings using Gemini (gemini-embedding-001).
5. Builds a local FAISS index.
6. Saves index + metadata to index/.

REQUIRES: GEMINI_API_KEY environment variable.
This is NOT part of evaluator runtime — the prebuilt index is committed.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.knowledge_loader import discover_documents
from src.retrieval.chunker import chunk_documents
from src.retrieval.embedder import embed_chunks, get_embedding_dimension
from src.retrieval.vector_store import VectorStore, INDEX_DIR, FAISS_PATH, METADATA_PATH, INDEX_META_PATH


def main():
    print("=" * 60)
    print("SmartResolve — FAISS Index Builder")
    print("=" * 60)

    print("\n[1/7] Loading knowledge documents...")
    documents = discover_documents()
    print(f"  Knowledge documents: {len(documents)}")
    if not documents:
        print("  ERROR: No documents found. Check knowledge/manifest.json")
        sys.exit(1)

    print("\n[2/7] Generating chunks...")
    chunks = chunk_documents(documents)
    print(f"  Chunks: {len(chunks)}")
    if not chunks:
        print("  ERROR: No chunks generated.")
        sys.exit(1)

    print("\n[3/7] Checking Gemini availability...")
    from src.ai.gemini_client import is_available
    if not is_available():
        print("  ERROR: GEMINI_API_KEY not set. Cannot generate embeddings.")
        print("  Set GEMINI_API_KEY environment variable and retry.")
        sys.exit(1)

    print("\n[4/7] Generating embeddings (gemini-embedding-001)...")
    print(f"  Embedding {len(chunks)} chunks in batches...")
    start = time.time()
    embeddings = embed_chunks(chunks, batch_size=32)
    elapsed = time.time() - start
    if embeddings is None:
        print("  ERROR: Embedding generation failed.")
        sys.exit(1)
    print(f"  Embeddings generated in {elapsed:.1f}s")

    dimension = len(embeddings[0])
    print(f"  Embedding dimension: {dimension}")

    print("\n[5/7] Building FAISS index...")
    import faiss
    import numpy as np

    vectors = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)
    print(f"  Index vectors: {index.ntotal}")

    print("\n[6/7] Saving index and metadata...")
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "section_heading": chunk["section_heading"],
            "category": chunk["category"],
            "chunk_index": chunk["chunk_index"],
            "content": chunk["content"],
        })

    meta_info = {
        "embedding_model": "gemini-embedding-001",
        "embedding_dimension": dimension,
        "index_version": "1.0",
        "knowledge_version": "1.0",
        "chunk_count": len(chunks),
        "document_count": len(documents),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    store = VectorStore()
    store.save(index, metadata, meta_info)

    print("\n[7/7] Verifying index...")
    loaded_store = VectorStore()
    if loaded_store.load():
        print(f"  Verification OK: {loaded_store.total_vectors} vectors, dimension {loaded_store.dimension}")
    else:
        print("  WARNING: Index verification failed")

    print("\n" + "=" * 60)
    print("Index generation complete!")
    print(f"  Documents: {len(documents)}")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Embedding dimension: {dimension}")
    print(f"  Index vectors: {index.ntotal}")
    print(f"  Index saved to: {INDEX_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
