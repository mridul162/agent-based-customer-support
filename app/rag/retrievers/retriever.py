"""
retriever.py

## Purpose:

Core retrieval component for the
Hasanah Mart multilingual RAG system.

## Responsibilities:

* Generate query embeddings
* Search FAISS vector store
* Return top-k relevant chunks

## Architecture Philosophy:

Retrieval-first design.
Simple orchestration.
No reranking or filtering.
"""

import logging

from app.config.settings import settings
from app.rag.embedders.openai_embedder import OpenAIEmbedder
from app.rag.models.retrieval_models import RetrievedChunk
from app.rag.vectorstores.faiss_store import FAISSStore

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# RETRIEVER
# ---------------------------------------------------------


class Retriever:
    """
    Semantic retriever using
    OpenAI embeddings + FAISS.
    """

    def __init__(
        self,
        embedder: OpenAIEmbedder,
        vector_store: FAISSStore,
    ):

        self.embedder = embedder

        self.vector_store = vector_store

        logger.info("Retriever initialized.")

    # -----------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Retrieve top-k relevant chunks.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        logger.info(f"Retrieving chunks for query: {query}")

        # ---------------------------------------------
        # Query Embedding
        # ---------------------------------------------

        query_embedding = self.embedder.embed_text(query)

        # ---------------------------------------------
        # Vector Search
        # ---------------------------------------------

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        retrieved_chunks = []

        for result in results:
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=result.score,
                    metadata=result.metadata,
                )
            )

        logger.info(f"Retrieved {len(retrieved_chunks)} chunks.")

        return retrieved_chunks


if __name__ == "__main__":
    embedder = OpenAIEmbedder()

    vector_store = FAISSStore(embedding_dimension=settings.embedding_dimension)

    vector_store.load(
        index_path=settings.faiss_index_path, metadata_path=settings.faiss_metadata_path
    )

    retriever = Retriever(embedder=embedder, vector_store=vector_store)

    query = "What are the benefits of khalisha honey?"

    results = retriever.retrieve(query=query, top_k=5)

    for result in results:
        print(result.metadata.get("document_id"))

        print(result.text)

        print(result.score)
