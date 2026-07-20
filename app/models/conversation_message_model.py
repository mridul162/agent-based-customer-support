"""
app/models/conversation_message.py

Purpose:
--------
SQLAlchemy ORM model for the conversation_messages table.

Responsibilities:
-----------------
- Store one message (user or assistant) from a customer conversation.
- Preserve insertion order via auto-incrementing primary key so history
  can be retrieved in chronological order with ORDER BY id.

This module DOES NOT:
---------------------
- Know about ConversationService or the graph.
- Import AgentState or any application-level schemas.

Ownership:
----------
    ConversationRepository reads/writes this model.
    ConversationService never imports this directly.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ConversationMessageDB(Base):
    __tablename__ = "conversation_messages"

    id:          Mapped[int]      = mapped_column(Integer,              primary_key=True, autoincrement=True)
    customer_id: Mapped[str]      = mapped_column(String,              nullable=False,   index=True)
    role:        Mapped[str]      = mapped_column(String(20),          nullable=False)   # "user" | "assistant"
    content:     Mapped[str]      = mapped_column(Text,                nullable=False)
    created_at:  Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ConversationMessageDB id={self.id} role={self.role} customer={self.customer_id}>"