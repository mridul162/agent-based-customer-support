from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]