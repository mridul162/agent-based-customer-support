"""
embedding_models.py

Purpose:
--------
Data models for embedding artifacts used in the
Hasanah Mart multilingual RAG system.

Responsibilities:
-----------------
- Define embedded chunk structures
- Preserve chunk-to-vector traceability
- Store embeddings with associated metadata
- Provide a consistent embedding artifact format

Architecture Philosophy:
------------------------
Simple data containers.
Metadata preservation.
Easy serialization and debugging.
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class EmbeddedChunk:
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]