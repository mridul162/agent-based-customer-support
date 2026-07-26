"""
openai_embedder.py

Purpose:
--------
OpenAI embedding wrapper for the
Hasanah Mart multilingual RAG system.

Responsibilities:
-----------------
- Generate embeddings using OpenAI API
- Support multilingual semantic retrieval
- Provide batch embedding support
- Normalize embedding outputs

Architecture Philosophy:
------------------------
Lightweight deployment.
API-based embeddings.
Render-friendly infrastructure.
"""

import logging

from app.config.settings import settings
from app.llm.openai_client import get_openai_client
from app.rag.embedders.base_embedder import BaseEmbedder

# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# OPENAI EMBEDDER
# ---------------------------------------------------------

class OpenAIEmbedder(BaseEmbedder):

    """
    OpenAI embedding generator.
    """

    # -----------------------------------------------------
    # INITIALIZATION
    # -----------------------------------------------------

    def __init__(
        self,
        model_name: str | None = None,
    ):

        self.model_name = (
            model_name
            or settings.embedding_model
        )

        self.client = get_openai_client()

        logger.info(
            f"Initialized OpenAI embedder: "
            f"{self.model_name}"
        )

    # -----------------------------------------------------
    # SINGLE TEXT EMBEDDING
    # -----------------------------------------------------

    def embed_text(
        self,
        text: str,
    ) -> list[float]:

        """
        Generate embedding for single text.
        """

        if not text.strip():

            raise ValueError(
                "Input text cannot be empty."
            )

        try:

            response = (
                self.client.embeddings.create(
                    model=self.model_name,
                    input=text,
                )
            )

            embedding = (
                response.data[0].embedding
            )

            return embedding

        except Exception:

            logger.exception(
                "Failed to generate embedding."
            )

            raise

    # -----------------------------------------------------
    # BATCH EMBEDDINGS
    # -----------------------------------------------------

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        """
        Generate embeddings for multiple texts.
        """

        if not texts:

            raise ValueError(
                "Input texts cannot be empty."
            )

        try:

            response = (
                self.client.embeddings.create(
                    model=self.model_name,
                    input=texts,
                )
            )

            embeddings = [
                item.embedding
                for item in response.data
            ]

            return embeddings

        except Exception:

            logger.exception(
                "Failed to generate batch embeddings."
            )

            raise


# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------

if __name__ == "__main__":

    embedder = OpenAIEmbedder()

    text = (
        "Pure Sundarbans honey is rich "
        "in antioxidants."
    )

    embedding = embedder.embed_text(text)

    print("\nEmbedding generated successfully.")

    print(
        f"Embedding dimension: "
        f"{len(embedding)}"
    )

    print(
        f"First 10 values:\n"
        f"{embedding[:10]}"
    )
