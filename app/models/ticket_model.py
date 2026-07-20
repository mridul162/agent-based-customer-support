"""
app/models/ticket.py

Purpose:
--------
SQLAlchemy ORM model for the tickets table.

Responsibilities:
-----------------
- Define the database schema for a support ticket.
- Map Python attributes to PostgreSQL columns.

This module DOES NOT:
---------------------
- Contain business logic.
- Know about TicketService or repositories.
- Import AgentState or any schema other than TicketStatus.

Ownership:
----------
    TicketRepository reads/writes this model.
    TicketService never imports this — it talks to the repository.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.schemas.ticket import TicketStatus


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id:   Mapped[str]          = mapped_column(String,           primary_key=True)
    customer_id: Mapped[str]          = mapped_column(String,           nullable=False, index=True)
    issue:       Mapped[str]          = mapped_column(Text,             nullable=False)
    status:      Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)
    created_at:  Mapped[datetime]     = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_id} status={self.status} customer={self.customer_id}>"