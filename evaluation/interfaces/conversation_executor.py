from __future__ import annotations

from typing import Any, Protocol

from app.schemas.agent import AgentResponse


class ConversationExecutor(Protocol):
    """
    Interface for executing a customer conversation.

    Implementations may execute:

    - Single support agent
    - LangGraph graph
    - Multi-agent system
    - REST API
    - Mock executor

    Evaluation runners depend only on this interface.
    """

    def execute(
        self,
        *,
        customer_id: str,
        message: str,
    ) -> AgentResponse:
        """
        Execute one customer message.

        Returns
        -------
        AgentResponse
            Raw execution result.

        Expected fields are implementation-defined, but should include
        everything required by the evaluator.
        """
        ...