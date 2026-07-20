"""
app/services/conversation_service.py

Purpose:
--------
Store and retrieve conversation history per customer.

Responsibilities:
-----------------
- Maintain per-customer conversation history in memory.
- Provide save, load, and append operations.
- Return typed ConversationMessage lists.

This module DOES NOT:
---------------------
- Know about AgentState or the graph.
- Generate responses or make LLM calls.
- Own business logic about tickets or orders.

Architecture:
-------------
Same pattern as TicketService: in-memory dict for Milestone 10,
replaced by PostgreSQL in a future milestone without changing node code.

    memory_loader_node → ConversationService.get_history(customer_id)
    memory_writer_node → ConversationService.append_turn(customer_id, ...)

The service is the single owner of persistence.
Nodes never store history themselves.

Technical debt (intentional):
------------------------------
In-memory storage resets on service restart.
Acceptable for Milestone 10 — PostgreSQL persistence comes later.
"""

from app.schemas.conversation_message import ConversationMessage


class ConversationService:
    """
    In-memory store of conversation history keyed by customer_id.

    Each customer's history is a list of ConversationMessages in
    chronological order (oldest first).
    """

    def __init__(self) -> None:
        # dict[customer_id, list[ConversationMessage]]
        self._history: dict[str, list[ConversationMessage]] = {}

    def get_history(self, customer_id: str) -> list[ConversationMessage]:
        """
        Return the full conversation history for a customer.

        Returns an empty list if the customer has no prior history.
        Never returns None — callers can always iterate the result.

        Args:
            customer_id: The customer's unique identifier.

        Returns:
            List of ConversationMessage, oldest first.
        """
        return list(self._history.get(customer_id, []))

    def append_turn(
        self,
        customer_id: str,
        user_message: str,
        assistant_response: str,
    ) -> None:
        """
        Append one user + assistant turn to the customer's history.

        Both messages are appended together so history always contains
        complete turns (no orphaned user messages without a response).

        Args:
            customer_id:        The customer's unique identifier.
            user_message:       The customer's raw message text.
            assistant_response: The agent's response text.
        """
        if customer_id not in self._history:
            self._history[customer_id] = []

        self._history[customer_id].append(
            ConversationMessage(role="user", content=user_message)
        )
        self._history[customer_id].append(
            ConversationMessage(role="assistant", content=assistant_response)
        )

    def clear_history(self, customer_id: str) -> None:
        """
        Clear all history for a customer.

        Used in testing and for future session management.
        """
        self._history.pop(customer_id, None)


# ---------------------------------------------------------------------------
# Module-level singleton.
# Shared across all nodes in the same process.
# Replaced by a per-request injected instance when PostgreSQL is introduced.
# ---------------------------------------------------------------------------
conversation_service = ConversationService()