"""
base_embedder.py

Purpose:
--------
Abstract interface for embedding providers used in the
Hasanah Mart multilingual RAG system.

Responsibilities:
-----------------
- Define a common embedding contract
- Standardize embedding operations
- Support interchangeable embedding providers

Architecture Philosophy:
------------------------
Simple abstraction.
Provider-independent pipeline.
Minimal implementation requirements.
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """
    Base interface for all embedding providers.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        """
        pass