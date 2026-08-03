"""
prompt_builder.py

Purpose:
--------
Construct generation prompts from user queries
and retrieved context.

Responsibilities:
-----------------
- Format retrieved chunks into LLM-readable context
- Organize context into structured documents
- Build user prompts
- Build OpenAI-compatible message payloads
- Isolate prompt construction from generation logic

This module DOES NOT:
---------------------
- perform retrieval
- rank retrieved chunks
- call embedding models
- call LLM APIs
- generate answers
- manage conversation memory

Architecture Philosophy:
------------------------
Prompt construction is a dedicated layer.

Retrieval provides information.
PromptBuilder structures information.
The LLM generates answers.

Keep formatting logic centralized,
deterministic, and easy to debug.
"""

import logging

from app.rag.models.retrieval_models import RetrievedChunk

from .answer_prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds prompts for answer generation.
    """

    def format_history(
        self,
        history,
    ) -> str:

        if history is None:
            return "No previous conversation."

        messages = getattr(history, "messages", history)

        if not messages:
            return "No previous conversation."

        lines = []

        for message in messages:
            role = getattr(message, "role", None)
            content = getattr(message, "content", None)

            lines.append(f"{str(role).title()}: {content}")

        return "\n".join(lines)

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """
        Convert retrieved chunks into a structured context block.
        """

        if not chunks:
            return "No relevant context found."

        documents = []

        for idx, chunk in enumerate(chunks, start=1):
            metadata = chunk.metadata or {}

            document_id = metadata.get(
                "document_id", metadata.get("product_id", "Unknown Document")
            )

            heading = metadata.get("heading", "General Information")

            document = (
                f"[Document {idx}]\n\n"
                f"Document: {document_id}\n"
                f"Section: {heading}\n\n"
                f"{chunk.text}"
            )

            documents.append(document)

        separator = "\n\n" + "-" * 50 + "\n\n"

        return separator.join(documents)

    def build_user_prompt(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        history: None,
    ) -> str:
        """
        Build the user prompt.
        """

        context = self.format_context(chunks)

        conversation_history = self.format_history(history)
        logger.debug(
            "Built grounded answer prompt.",
            extra={
                "query": query,
                "context_documents": len(chunks),
                "has_history": history is not None,
            },
        )

        return USER_PROMPT_TEMPLATE.format(
            history=conversation_history,
            context=context,
            query=query,
        )

    def build_messages(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        history: None,
    ) -> list[dict]:
        """
        Build OpenAI-compatible messages.
        """

        user_prompt = self.build_user_prompt(
            query=query,
            chunks=chunks,
            history=history,
        )

        return [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
