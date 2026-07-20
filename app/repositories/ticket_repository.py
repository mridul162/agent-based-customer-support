"""
app/repositories/ticket_repository.py

Purpose:
--------
Data access layer for tickets. The only layer that knows SQLAlchemy.

Responsibilities:
-----------------
- create_ticket(): insert a new Ticket row and return a TicketResponse.
- get_ticket():    fetch a Ticket by ID and return a TicketResponse, or None.
- update_status(): change a ticket's status and return an updated TicketResponse.

This module DOES NOT:
---------------------
- Generate ticket IDs (caller provides them).
- Own business rules (TicketService owns those).
- Know about agents, nodes, or graph execution.
- Own transaction management.
- Call commit() or rollback().

Architecture:
-------------
    TicketService
          ↓
    TicketRepository    ← this file
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

Why return TicketResponse (not the ORM model)?
----------------------------------------------
Returning ORM objects would leak SQLAlchemy into the service
layer. The service would need to understand session lifetime,
lazy loading, and detached-instance behavior.

Mapping to TicketResponse keeps SQLAlchemy isolated inside the
repository layer.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ticket_model import Ticket
from app.schemas.ticket import TicketResponse, TicketStatus


class TicketRepository:
    """
    Manages persistence for support tickets.

    The repository is responsible only for data access and ORM mapping.

    Transaction management is intentionally handled outside the repository.
    Methods may add, update, query, or delete ORM objects, but must never
    call commit() or rollback().

    A transaction-scoped session is provided by the caller.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_ticket(
        self,
        ticket_id:   str,
        customer_id: str,
        issue:       str,
    ) -> TicketResponse:
        """
        Insert a new ticket row and return it as a TicketResponse.

        Args:
            ticket_id:   Caller-generated unique ID (e.g. "TICKET-ABC123").
            customer_id: The customer's identifier.
            issue:       The customer's issue description.

        Returns:
            TicketResponse with status=OPEN and created_at set.
        """
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            issue=issue,
            status=TicketStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )

        self._session.add(ticket)

        return self._to_response(ticket)

    def get_ticket(self, ticket_id: str) -> TicketResponse | None:
        """
        Fetch a ticket by ID.

        Returns:
            TicketResponse if found, None otherwise.
        """
        ticket = self._session.get(Ticket, ticket_id)
        if ticket is None:
            return None
        return self._to_response(ticket)

    def update_status(
        self,
        ticket_id:      str,
        status:         TicketStatus,
        agent_response: str | None = None,
    ) -> TicketResponse | None:
        """
        Update a ticket's status (and optionally agent_response).

        Returns:
            Updated TicketResponse, or None if ticket not found.
        """
        ticket = self._session.get(Ticket, ticket_id)
        if ticket is None:
            return None
        
        ticket.status = status

        return self._to_response(ticket)

    @staticmethod
    def _to_response(ticket: Ticket) -> TicketResponse:
        """Map ORM Ticket → TicketResponse. Keeps SQLAlchemy out of the service layer."""
        return TicketResponse(
            ticket_id=ticket.ticket_id,
            customer_id=ticket.customer_id,
            issue=ticket.issue,
            status=ticket.status,
            agent_response=None,   # not stored in DB yet — future migration adds this column
        )