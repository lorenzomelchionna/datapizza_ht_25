"""Ingest Codice Galattico, Manuale di Cucina, and Blogpost HTML into Qdrant.

Creates 3 separate collections for targeted RAG retrieval by specialized agents.

Usage:
    cd <project_root>
    ./pizza_env/bin/python -m hackapizza_solution.data_preparation.ingest_rag
"""

import os
import sys
from pathlib import Path

from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.cohere import CohereEmbedder
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import RecursiveSplitter, TextSplitter
from datapizza.pipeline.pipeline import IngestionPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import (
    COHERE_API_KEY, COHERE_ENDPOINT, QDRANT_HOST, QDRANT_PORT,
    EMBED_MODEL, EMBED_DIM,
    CODICE_PDF, MANUALE_PDF, BLOGPOST_DIR,
    COLLECTION_CODICE, COLLECTION_MANUALE, COLLECTION_BLOG,
)

load_dotenv()

VECTOR_NAME = "embedding_vector"


def _make_embedder() -> ChunkEmbedder:
    return ChunkEmbedder(
        client=CohereEmbedder(
            api_key=COHERE_API_KEY,
            base_url=COHERE_ENDPOINT,
            model_name=EMBED_MODEL,
            input_type="search_documents",
        ),
        embedding_name=VECTOR_NAME,
    )


def _make_vector_store(collection_name: str) -> QdrantVectorstore:
    vs = QdrantVectorstore(host=QDRANT_HOST, port=QDRANT_PORT)
    vs.create_collection(
        collection_name=collection_name,
        vector_config=[VectorConfig(dimensions=EMBED_DIM, name=VECTOR_NAME)],
    )
    return vs


def ingest_pdf(file_path: Path, collection_name: str):
    """Parse a PDF, split, embed, and store in Qdrant."""
    print(f"\nIngesting {file_path.name} -> collection '{collection_name}'")
    parser = DoclingParser()
    splitter = RecursiveSplitter(max_char=2000, overlap=100)
    embedder = _make_embedder()
    vector_store = _make_vector_store(collection_name)

    pipeline = IngestionPipeline(
        modules=[parser, splitter, embedder],
        vector_store=vector_store,
        collection_name=collection_name,
    )
    pipeline.run(file_path=str(file_path))
    print(f"  Done: {file_path.name}")


def ingest_html_files(directory: Path, collection_name: str):
    """Parse HTML files, split, embed, and store in Qdrant."""
    print(f"\nIngesting HTML from {directory} -> collection '{collection_name}'")
    splitter = TextSplitter(max_char=2000, overlap=100)
    embedder = _make_embedder()
    vector_store = _make_vector_store(collection_name)

    for html_file in sorted(directory.glob("*.html")):
        print(f"  Processing {html_file.name}...")
        from bs4 import BeautifulSoup
        text = BeautifulSoup(
            html_file.read_text(encoding="utf-8"), "html.parser"
        ).get_text()

        split_chunks = splitter.split(text)
        for chunk in split_chunks:
            chunk.metadata["source"] = html_file.name
        embedded_chunks = embedder.run(nodes=split_chunks)
        vector_store.add(embedded_chunks, collection_name)
    print(f"  Done: HTML files")


def run():
    ingest_pdf(CODICE_PDF, COLLECTION_CODICE)
    ingest_pdf(MANUALE_PDF, COLLECTION_MANUALE)
    ingest_html_files(BLOGPOST_DIR, COLLECTION_BLOG)
    print("\nAll ingestion complete!")


if __name__ == "__main__":
    run()
