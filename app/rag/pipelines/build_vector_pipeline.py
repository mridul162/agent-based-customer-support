"""
build_vector_pipeline.py

Purpose:
--------
Complete embedding pipeline integration for the
Hasanah Mart multilingual RAG system.

Pipeline:
---------
1. Load chunk artifacts
2. Generate OpenAI embeddings
3. Build embedded chunk records
4. Create FAISS vector store
5. Index embedded chunks
6. Save FAISS index and metadata artifacts

Architecture:
--------------
KB Validator
    ↓
Chunk Artifact Loader
    ↓
OpenAI Embedder
    ↓
FAISS Vector Store
"""

import logging

from app.config.settings import settings
from app.rag.embedders.openai_embedder import OpenAIEmbedder
from app.rag.models.embedding_models import EmbeddedChunk
from app.rag.pipelines.chunk_loader import ChunkArtifactLoader
from app.rag.utils.hashing import generate_product_hash
from app.rag.utils.manifest_manager import ManifestManager
from app.rag.vectorstores.faiss_store import FAISSStore

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Group Chunk by Products
# ----------------------------------------


# ---------------------------------------------------------
# VECTOR PIPELINE
# ---------------------------------------------------------

class VectorPipeline:

    """
    End-to-end ingestion pipeline.
    """

    # -----------------------------------------------------

    def __init__(self):

        logger.info(
            "Initializing vector pipeline..."
        )


        # -------------------------------------------------
        # EMBEDDER
        # -------------------------------------------------

        self.embedder = (
            OpenAIEmbedder()
        )

        self.chunk_loader = (
            ChunkArtifactLoader(
                chunk_root=settings.chunk_artifacts_path
            )
        )

        self.manifest_manager = (
            ManifestManager(
                settings.manifest_path
            )
        )

        logger.info(
            "OpenAI embedder initialized."
        )

    def group_chunks_by_product(
        self,
        chunks: list[dict]
    ) -> dict:

        products = {}

        for chunk in chunks:

            document_id = (
                chunk["metadata"]
                ["document_id"]
            )

            products.setdefault(
                document_id,
                []
            ).append(chunk)

        return products


    def get_changed_products(
        self,
        products: dict,
        manifest: dict
    ) -> dict:

        changed_products = {}

        for product_id, chunks in products.items():

            current_hash = (
                generate_product_hash(
                    chunks
                )
            )

            stored_hash = (
                manifest.get(
                    product_id
                )
            )

            if current_hash != stored_hash:

                changed_products[
                    product_id
                ] = {

                    "chunks": chunks,

                    "hash": current_hash
                }

        return changed_products
    # -----------------------------------------------------

    def run(self):

        logger.info(
            "Loading chunk artifacts..."
        )

        chunks = self.chunk_loader.load()

        if not chunks:
            raise ValueError(
                "No chunk artifacts found."
            )
        
        # ============================================
        # Grouping Chunk by Product
        # ============================================

        products = (
            self.group_chunks_by_product(
                chunks
            )
        )

        print(
            f"Products: {len(products)}"
        )

        for product_id, product_chunks in products.items():

            print(
                product_id,
                len(product_chunks)
            )

        # ============================================
        # TEMPORARY HASH TEST
        # ============================================

        manifest = (
            self.manifest_manager.load()
        )

        changed_products = (
            self.get_changed_products(
                products,
                manifest
            )
        )

        if not changed_products:

            logger.info(
                "No product changes detected. "
                "Skipping vector rebuild."
            )

            return

        for product_id, data in changed_products.items():

            manifest[product_id] = data["hash"]

        self.manifest_manager.save(
            manifest
        )

        print(
            f"Changed Products: "
            f"{len(changed_products)}"
        )

        # =================================================
        # STEP 1: GENERATE EMBEDDINGS
        # =================================================

        logger.info(
            "Generating embeddings..."
        )

        chunk_texts = [

            chunk["text"]

            for chunk in chunks
        ]

        embeddings = (
            self.embedder.embed_batch(
                chunk_texts
            )
        )

        logger.info(
            "Embeddings generated successfully."
        )

        logger.info(
            f"Embedding dimension: "
            f"{len(embeddings[0])}"
        )

        # =================================================
        # STEP 2: BUILD EMBEDDED CHUNKS
        # =================================================

        logger.info(
            "Building embedded chunks..."
        )

        embedded_chunks = []

        for chunk, embedding in zip(
            chunks,
            embeddings
        ):

            embedded_chunk = (
                EmbeddedChunk(

                    chunk_id=(
                        chunk["chunk_id"]
                    ),

                    text=chunk["text"],

                    embedding=embedding,

                    metadata=chunk["metadata"]
                )
            )

            embedded_chunks.append(
                embedded_chunk
            )

        logger.info(
            f"Created "
            f"{len(embedded_chunks)} "
            f"embedded chunks."
        )

        # =================================================
        # STEP 3: BUILD VECTOR STORE
        # =================================================

        logger.info(
            "Building FAISS vector store..."
        )

        vector_store = FAISSStore(
            embedding_dimension=(
                len(embeddings[0])
            )
        )

        vector_store.add_embeddings(
            embedded_chunks
        )

        logger.info(
            f"Indexed "
            f"{vector_store.total_vectors()} "
            f"vectors."
        )

        # =================================================
        # STEP 4: SAVE ARTIFACTS
        # =================================================

        logger.info(
            "Saving vector database..."
        )

        vector_store.save(

            index_path=(
                settings.faiss_index_path
            ),

            metadata_path=(
                settings.faiss_metadata_path
            )
        )

        logger.info(
            "Vector database saved successfully."
        )

        logger.info(
            "Pipeline completed successfully."
        )


# ---------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------

if __name__ == "__main__":

    pipeline = VectorPipeline()

    pipeline.run()
