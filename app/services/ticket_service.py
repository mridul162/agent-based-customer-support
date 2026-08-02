"""
app/services/ticket_service.py  (Milestone 11.5 - session management fix)

Public API:
    create_ticket(request) -> TicketResponse
    get_ticket(ticket_id)  -> TicketResponse | None
    list_tickets(limit)    -> list[TicketResponse]
    update_ticket(ticket_id, request) -> TicketResponse | None
"""

import uuid

from app.database.connection import get_session
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import CreateTicketRequest, TicketResponse, UpdateTicketRequest


class TicketService:
    """
    Orchestrates ticket lifecycle. Delegates persistence to TicketRepository.
    Does not know SQLAlchemy exists.
    """

    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        with get_session() as session:
            return TicketRepository(session).create_ticket(
                ticket_id=ticket_id,
                customer_id=request.customer_id,
                issue=request.issue,
            )

    def get_ticket(self, ticket_id: str) -> TicketResponse | None:
        with get_session() as session:
            return TicketRepository(session).get_ticket(ticket_id)

    def list_tickets(self, limit: int = 20) -> list[TicketResponse]:
        with get_session() as session:
            return TicketRepository(session).list_tickets(limit=limit)

    def update_ticket(
        self,
        ticket_id: str,
        request: UpdateTicketRequest,
    ) -> TicketResponse | None:
        if request.status is None:
            return self.get_ticket(ticket_id)
        with get_session() as session:
            return TicketRepository(session).update_status(
                ticket_id=ticket_id,
                status=request.status,
                agent_response=request.agent_response,
            )
