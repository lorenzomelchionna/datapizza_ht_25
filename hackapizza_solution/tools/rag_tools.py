"""RAG query tool: embed a question and retrieve relevant chunks from Qdrant."""

import os
from pathlib import Path

from datapizza.embedders.cohere import CohereEmbedder
from datapizza.vectorstores.qdrant import QdrantVectorstore
from datapizza.tools import tool
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import (
    COHERE_API_KEY, COHERE_ENDPOINT, QDRANT_HOST, QDRANT_PORT,
    EMBED_MODEL, COLLECTION_CODICE, COLLECTION_MANUALE, COLLECTION_BLOG,
)

load_dotenv()

_embedder = None
_retriever = None


def _get_embedder() -> CohereEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = CohereEmbedder(
            api_key=COHERE_API_KEY,
            base_url=COHERE_ENDPOINT,
            model_name=EMBED_MODEL,
            input_type="search_query",
        )
    return _embedder


def _get_retriever() -> QdrantVectorstore:
    global _retriever
    if _retriever is None:
        _retriever = QdrantVectorstore(host=QDRANT_HOST, port=QDRANT_PORT)
    return _retriever


def _rag_query(query: str, collection_name: str, k: int = 5) -> str:
    """Embed query and retrieve top-k chunks from a Qdrant collection."""
    embedder = _get_embedder()
    retriever = _get_retriever()

    query_vector = embedder.run(text=query)
    results = retriever.search(
        collection_name=collection_name,
        query_vector=query_vector,
        vector_name="embedding_vector",
        k=k,
    )
    if not results:
        return f"No result found in collection '{collection_name}' for: {query}"

    chunks_text = []
    for i, chunk in enumerate(results, 1):
        chunks_text.append(f"[{i}] {chunk.text}")
    return "\n\n".join(chunks_text)


@tool
def query_codice_galattico(query: str) -> str:
    """Search the Codice Galattico for information about regulations, limits, licenses,
    protected orders, and legal requirements for intergalactic dining."""
    return _rag_query(query, COLLECTION_CODICE)


@tool
def query_manuale_cucina(query: str) -> str:
    """Search the Manuale di Cucina di Sirius Cosmo for information about
    cooking techniques, technique categories, license types and levels,
    and the three professional orders."""
    return _rag_query(query, COLLECTION_MANUALE)


@tool
def query_blogposts(query: str) -> str:
    """Search the blogpost reviews for information about specific dishes,
    ingredient percentages, and restaurant reviews."""
    return _rag_query(query, COLLECTION_BLOG)
