"""
Persist and search embedding vectors for the support RAG system.

The class keeps the copied project's FAISSStore name so the surrounding RAG
code does not need to change, but this implementation is pure Python. That
keeps the customer-support app easy to run without native FAISS dependencies.
"""

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.models.embedding_models import EmbeddedChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    Semantic retrieval result.
    """

    score: float
    chunk_id: str
    text: str
    metadata: dict[str, Any]


class FAISSStore:
    """
    Simple persisted vector store with cosine-similarity search.
    """

    def __init__(
        self,
        embedding_dimension: int,
    ):
        self.embedding_dimension = embedding_dimension
        self.vector_store: list[list[float]] = []
        self.metadata_store: list[dict[str, Any]] = []

    def add_embeddings(
        self,
        embedded_chunks: list[EmbeddedChunk],
    ):
        """
        Add embedded chunks to the in-memory vector store.
        """

        for chunk in embedded_chunks:
            if len(chunk.embedding) != self.embedding_dimension:
                raise ValueError(
                    "Embedding dimension mismatch: "
                    f"expected {self.embedding_dimension}, "
                    f"got {len(chunk.embedding)}"
                )

            self.vector_store.append(chunk.embedding)
            self.metadata_store.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            })

        logger.info(
            "Added %s embeddings to vector store.",
            len(embedded_chunks),
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Perform cosine-similarity search.
        """

        if len(query_embedding) != self.embedding_dimension:
            raise ValueError(
                "Query embedding dimension mismatch: "
                f"expected {self.embedding_dimension}, "
                f"got {len(query_embedding)}"
            )

        scored_results = []

        for index_position, vector in enumerate(self.vector_store):
            score = self._cosine_similarity(query_embedding, vector)
            metadata_item = self.metadata_store[index_position]

            scored_results.append(
                RetrievalResult(
                    score=score,
                    chunk_id=metadata_item["chunk_id"],
                    text=metadata_item["text"],
                    metadata=metadata_item["metadata"],
                )
            )

        return sorted(
            scored_results,
            key=lambda result: result.score,
            reverse=True,
        )[:top_k]

    def save(
        self,
        index_path: str,
        metadata_path: str,
    ):
        """
        Persist vectors and metadata as JSON artifacts.
        """

        index_file = Path(index_path)
        metadata_file = Path(metadata_path)

        index_file.parent.mkdir(parents=True, exist_ok=True)
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        with open(index_file, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "embedding_dimension": self.embedding_dimension,
                    "vectors": self.vector_store,
                },
                file,
            )

        with open(metadata_file, "w", encoding="utf-8") as file:
            json.dump(
                self.metadata_store,
                file,
                ensure_ascii=False,
                indent=2,
            )

        logger.info("Vector store saved.")

    def load(
        self,
        index_path: str,
        metadata_path: str,
    ):
        """
        Load persisted vectors and metadata.
        """

        index_file = Path(index_path)
        metadata_file = Path(metadata_path)

        if not index_file.exists() or not metadata_file.exists():
            raise FileNotFoundError(
                f"Missing vector artifacts: {index_file}, {metadata_file}"
            )

        with open(index_file, "r", encoding="utf-8") as file:
            index_payload = json.load(file)

        with open(metadata_file, "r", encoding="utf-8") as file:
            self.metadata_store = json.load(file)

        self.embedding_dimension = index_payload["embedding_dimension"]
        self.vector_store = index_payload["vectors"]

        logger.info("Vector store loaded.")

    def total_vectors(self) -> int:
        """
        Return total indexed vectors.
        """

        return len(self.vector_store)

    @staticmethod
    def _cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:
        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot_product / (left_norm * right_norm)
