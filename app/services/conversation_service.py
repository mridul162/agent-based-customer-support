"""
app/services/conversation_service.py

Purpose:
--------
Manage conversation history for customers.

Responsibilities:
-----------------
- Retrieve conversation history.
- Append conversation turns.
- Clear conversation history (tests/admin operations).
- Define transaction boundaries for conversation operations.

This service DOES NOT:
----------------------
- Execute SQL directly (except temporary maintenance operations).
- Know ORM implementation details.
- Manage commits or rollbacks manually.
- Contain agent logic.

Architecture:
-------------
    Agent / API
          ↓
    ConversationService
          ↓
    ConversationRepository
          ↓
      SQLAlchemy

Session Management:
-------------------
Every public method executes inside a transaction-scoped session
provided by get_session().

Transaction behavior:

    Success:
        commit automatically

    Failure:
        rollback automatically

    Always:
        session closes automatically

Repositories are responsible only for persistence operations.
Transaction ownership belongs to the service layer.
"""

from app.database.connection import get_session
from app.models.conversation_message_model import ConversationMessageDB
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation_message import ConversationMessage


class ConversationService:
    """
    Service layer for conversation history management.

    Delegates persistence to ConversationRepository while owning
    transaction boundaries through get_session().
    """

    def get_history(
        self,
        customer_id: str,
    ) -> list[ConversationMessage]:
        with get_session() as session:
            return ConversationRepository(session).get_history(customer_id)

    def append_turn(
        self,
        customer_id: str,
        user_message: str,
        assistant_response: str,
    ) -> None:
        with get_session() as session:
            ConversationRepository(session).append_turn(
                customer_id=customer_id,
                user_message=user_message,
                assistant_response=assistant_response,
            )

    def clear_history(self, customer_id: str) -> None:
        """
        Delete all messages for a customer.
        Args:
            customer_id: The customer's unique identifier.
        """
        with get_session() as session:
            ConversationRepository(session).clear_history(customer_id)


# ---------------------------------------------------------------------------
# Module-Level Singleton
#
# Preserves the same interface used throughout the application.
# ---------------------------------------------------------------------------

conversation_service = ConversationService()