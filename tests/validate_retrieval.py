"""
tests/validate_retrieval.py

Purpose:
--------
Validate the current retrieval system after integrating the copied RAG package.

This developer validation verifies that:
- The flat customer-support KB is ingested into chunk artifacts.
- The persisted vector store can save, load, and rank chunks.
- RetrievalPipeline loads configured artifacts and preserves metadata.
- RetrievalService returns a graceful response when the index is missing.
- retrieve_knowledge_tool is registered in the app tool registry.

The script avoids live OpenAI calls by using a deterministic fake embedder.
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import settings
from app.rag.models.embedding_models import EmbeddedChunk
from app.rag.pipelines.chunk_loader import ChunkArtifactLoader
from app.rag.pipelines.ingestion_pipeline import IngestionPipeline
from app.rag.pipelines.retrieval_pipeline import RetrievalPipeline
from app.rag.vectorstores.faiss_store import FAISSStore
from app.services import retrieval_service
from app.services.retrieval_service import RetrievalService
from app.tools.tool_registry import TOOL_REGISTRY


PASS = "PASS"
FAIL = "FAIL"


def check(condition: bool, message: str) -> None:
    status = PASS if condition else FAIL
    symbol = "[OK]" if condition else "[FAIL]"
    print(f"  {symbol} {status:<6} {message}")

    if not condition:
        raise AssertionError(message)


class FakeEmbedder:
    """
    Deterministic embedding stub for offline retrieval validation.
    """

    dimension = 3

    def embed_text(self, text: str) -> list[float]:
        lowered = text.lower()

        if "refund" in lowered or "return" in lowered:
            return [1.0, 0.0, 0.0]

        if "shipping" in lowered or "delivery" in lowered:
            return [0.0, 1.0, 0.0]

        return [0.0, 0.0, 1.0]


def _set_retrieval_settings(
    *,
    chunk_path: str,
    index_path: str,
    metadata_path: str,
) -> tuple[str, str, str, int]:
    previous = (
        settings.chunk_artifacts_path,
        settings.faiss_index_path,
        settings.faiss_metadata_path,
        settings.embedding_dimension,
    )

    settings.chunk_artifacts_path = chunk_path
    settings.faiss_index_path = index_path
    settings.faiss_metadata_path = metadata_path
    settings.embedding_dimension = FakeEmbedder.dimension

    return previous


def _restore_retrieval_settings(previous: tuple[str, str, str, int]) -> None:
    (
        settings.chunk_artifacts_path,
        settings.faiss_index_path,
        settings.faiss_metadata_path,
        settings.embedding_dimension,
    ) = previous

    retrieval_service._get_answer_generator.cache_clear()


def _build_test_vector_artifacts(
    *,
    index_path: str,
    metadata_path: str,
) -> None:
    store = FAISSStore(embedding_dimension=FakeEmbedder.dimension)

    store.add_embeddings([
        EmbeddedChunk(
            chunk_id="returns_refund__refund.md__0__0",
            text="Refunds are reviewed after the returned item is received.",
            embedding=[1.0, 0.0, 0.0],
            metadata={
                "document_id": "returns_refund",
                "category": "returns",
                "source_file": "refund.md",
                "heading": "Refund Policy",
            },
        ),
        EmbeddedChunk(
            chunk_id="shipping_shipping__shipping.md__0__0",
            text="Shipping updates are sent when an order is dispatched.",
            embedding=[0.0, 1.0, 0.0],
            metadata={
                "document_id": "shipping_shipping",
                "category": "shipping",
                "source_file": "shipping.md",
                "heading": "Shipping",
            },
        ),
    ])

    store.save(
        index_path=index_path,
        metadata_path=metadata_path,
    )


def validate_ingestion_outputs() -> None:
    print("[1] KB ingestion artifacts")

    IngestionPipeline(kb_root=settings.knowledge_base_path).run()

    chunks = ChunkArtifactLoader(
        chunk_root=settings.chunk_artifacts_path
    ).load()

    check(len(chunks) > 0, "Chunk artifacts were generated")
    check(
        all("document_id" in chunk["metadata"] for chunk in chunks),
        "Chunks preserve document_id metadata",
    )
    check(
        all("category" in chunk["metadata"] for chunk in chunks),
        "Chunks preserve category metadata",
    )


def validate_vector_store() -> None:
    print("[2] Vector store save/load/search")

    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = str(Path(temp_dir) / "index.json")
        metadata_path = str(Path(temp_dir) / "metadata.json")

        _build_test_vector_artifacts(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        store = FAISSStore(embedding_dimension=FakeEmbedder.dimension)
        store.load(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        results = store.search([1.0, 0.0, 0.0], top_k=2)

        check(store.total_vectors() == 2, "Persisted vectors load correctly")
        check(len(results) == 2, "Search returns requested ranked results")
        check(
            results[0].metadata["category"] == "returns",
            "Refund query ranks returns chunk first",
        )


def validate_retrieval_pipeline() -> None:
    print("[3] RetrievalPipeline with fake embedder")

    with tempfile.TemporaryDirectory() as temp_dir:
        index_path = str(Path(temp_dir) / "index.json")
        metadata_path = str(Path(temp_dir) / "metadata.json")

        _build_test_vector_artifacts(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        previous = _set_retrieval_settings(
            chunk_path=settings.chunk_artifacts_path,
            index_path=index_path,
            metadata_path=metadata_path,
        )

        try:
            with patch(
                "app.rag.pipelines.retrieval_pipeline.OpenAIEmbedder",
                FakeEmbedder,
            ):
                pipeline = RetrievalPipeline()

                start = time.perf_counter()
                results = pipeline.retrieve(
                    query="What is your refund policy?",
                    top_k=2,
                )
                elapsed_ms = (time.perf_counter() - start) * 1000

            check(len(results) == 2, "Pipeline retrieves chunks")
            check(results[0].metadata["category"] == "returns", "Ranking works")
            check(results[0].text.strip() != "", "Chunk text is available")
            check(results[0].score is not None, "Similarity score is recorded")

            print(f"  Retrieved : {len(results)} chunks")
            print(f"  Latency   : {elapsed_ms:.2f} ms")

        finally:
            _restore_retrieval_settings(previous)


def validate_service_and_tool_wiring() -> None:
    print("[4] Service fallback and tool registry")

    with tempfile.TemporaryDirectory() as temp_dir:
        previous = _set_retrieval_settings(
            chunk_path=settings.chunk_artifacts_path,
            index_path=str(Path(temp_dir) / "missing-index.json"),
            metadata_path=str(Path(temp_dir) / "missing-metadata.json"),
        )

        try:
            retrieval_service._get_answer_generator.cache_clear()

            with patch(
                "app.rag.pipelines.retrieval_pipeline.OpenAIEmbedder",
                FakeEmbedder,
            ), patch.object(retrieval_service.logger, "exception"):
                answer = RetrievalService.answer_question(
                    "What is your warranty policy?"
                )

            check(
                "retrieval index has not been built" in answer,
                "Service handles missing vector artifacts gracefully",
            )

        finally:
            _restore_retrieval_settings(previous)

    spec = TOOL_REGISTRY.get("retrieve_knowledge_tool")

    check(spec is not None, "retrieve_knowledge_tool is registered")
    assert spec is not None
    check(spec.required_arguments == (), "Retrieval tool needs no extracted args")


def main() -> None:
    print("=" * 64)
    print("  Retrieval System Validation")
    print("=" * 64)
    print()

    validate_ingestion_outputs()
    print()

    validate_vector_store()
    print()

    validate_retrieval_pipeline()
    print()

    validate_service_and_tool_wiring()
    print()

    print("=" * 64)
    print("  Retrieval Validation Completed")
    print("=" * 64)


if __name__ == "__main__":
    main()
