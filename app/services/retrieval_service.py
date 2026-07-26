"""
Application-facing retrieval service.
"""

import logging
from functools import lru_cache

from app.rag.generators.answer_generator import AnswerGenerator
from app.rag.pipelines.retrieval_pipeline import RetrievalPipeline

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_answer_generator() -> AnswerGenerator:
    return AnswerGenerator(
        retrieval_pipeline=RetrievalPipeline()
    )


class RetrievalService:
    """
    Thin facade over the RAG package for support tools and nodes.
    """

    @staticmethod
    def answer_question(
        question: str,
        top_k: int = 5,
    ) -> str:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        logger.info("Retrieving KB answer.")

        try:
            generator = _get_answer_generator()
            return generator.generate(
                query=question,
                history=None,
                top_k=top_k,
            )
        except FileNotFoundError:
            logger.exception("RAG vector artifacts are missing.")
            return (
                "I could not search the knowledge base yet because the "
                "retrieval index has not been built. I can create a support "
                "ticket so a specialist can help with this."
            )
