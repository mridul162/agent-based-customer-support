"""
app/repositories/conversation_repository.py

Purpose:
--------
Data access layer for conversation history. The only layer that
knows about the ConversationMessageDB ORM model.

Responsibilities:
-----------------
- append_turn():  insert user + assistant messages for one conversation turn.
- get_history():  return all messages for a customer in chronological order.
- clear_history(): delete all messages for a customer.

This module DOES NOT:
---------------------
- Know about ConversationService business logic.
- Know about agents, nodes, or graph execution.
- Own transaction management.
- Call commit() or rollback().
- Import AgentState or application-level orchestration code.

Architecture:
-------------
    ConversationService
          ↓
    ConversationRepository    ← this file
          ↓
    SQLAlchemy ORM
          ↓
    PostgreSQL

Transaction Ownership:
----------------------
The repository performs database operations only.

Transaction boundaries belong to the service layer via:

    with get_session() as session:

The service layer is responsible for:

    - commit
    - rollback
    - session lifecycle

Repositories should never call:

    session.commit()
    session.rollback()

Why return list[ConversationMessage] (not ORM objects)?
-------------------------------------------------------
The service layer should not be exposed to SQLAlchemy models,
session lifecycle concerns, lazy loading, or detached-instance
behavior.

ConversationMessage is the clean schema type already used by
the rest of the application.
"""
from datetime import datetime, timezone

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.models.conversation_message_model import ConversationMessageDB
from app.schemas.conversation_message import ConversationMessage


class ConversationRepository:
    
    """
    Manages persistence for conversation history.

    The repository is responsible only for data access and ORM mapping.

    Transaction management is intentionally handled outside the repository.
    Methods may insert, query, or delete ORM objects, but must never call
    commit() or rollback().

    A transaction-scoped session is provided by the caller.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def append_turn(
        self,
        customer_id:        str,
        user_message:       str,
        assistant_response: str,
    ) -> None:
        """
        Persist one conversation turn (user message + assistant response).

        Both messages are inserted in the same transaction so history
        always contains complete turns.

        Args:
            customer_id:        The customer's unique identifier.
            user_message:       The raw customer message text.
            assistant_response: The agent's response text.
        """
        now = datetime.now(timezone.utc)

        self._session.add(ConversationMessageDB(
            customer_id=customer_id,
            role="user",
            content=user_message,
            created_at=now,
        ))
        self._session.add(ConversationMessageDB(
            customer_id=customer_id,
            role="assistant",
            content=assistant_response,
            created_at=now,
        ))

    def get_history(self, customer_id: str) -> list[ConversationMessage]:
        """
        Return all messages for a customer in chronological order.

        ORDER BY id ASC ensures insertion order regardless of timestamp
        precision — two messages inserted in the same transaction have
        the same created_at but different autoincrement IDs.

        Returns:
            List of ConversationMessage, oldest first.
            Empty list if the customer has no history.
        """
        rows = (
            self._session.query(ConversationMessageDB)
            .filter(ConversationMessageDB.customer_id == customer_id)
            .order_by(asc(ConversationMessageDB.id))
            .all()
        )
        return [
            ConversationMessage(role=row.role, content=row.content)  # type: ignore[arg-type]
            for row in rows
        ]
    
    def clear_history(self, customer_id: str) -> None:
        """
        Delete all messages for a customer.
        Primarily used by tests.
        """
        self._session.query(
            ConversationMessageDB
        ).filter(
            ConversationMessageDB.customer_id == customer_id
        ).delete()