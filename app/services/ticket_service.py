"""
app/services/ticket_service.py  (Milestone 11.5 — session management fix)

Change from Milestone 11:
    Before: return TicketRepository(SessionLocal())
            # session never explicitly closed — connection leak risk

    After:  with SessionLocal() as session:
                repo = TicketRepository(session)
                result = repo.operation(...)
            return result
            # session closed on context manager exit, even on exception

Public API is unchanged:
    create_ticket(request) -> TicketResponse
    get_ticket(ticket_id)  -> TicketResponse | None
    list_tickets()         -> list[TicketResponse]
    update_ticket(ticket_id, request) -> TicketResponse | None

No nodes or tools change.
"""

import uuid

from app.database.connection import get_session
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import CreateTicketRequest, TicketResponse, UpdateTicketRequest


class TicketService:
    """
    Orchestrates ticket lifecycle. Delegates persistence to TicketRepository.
    Does not know SQLAlchemy exists.

    Session management:
        Each public method opens one session via `with get_session() as session`.
        The context manager guarantees the session is closed on exit — whether
        the operation succeeds or raises an exception.
        When FastAPI request-scoped injection arrives, the session will be
        injected rather than opened here — the repository interface is unchanged.
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

    def list_tickets(self) -> list[TicketResponse]:
        # TODO: add TicketRepository.list_all() — returns [] for now.
        return []

    def update_ticket(
        self,
        ticket_id: str,
        request:   UpdateTicketRequest,
    ) -> TicketResponse | None:
        if request.status is None:
            return self.get_ticket(ticket_id)
        with get_session() as session:
            return TicketRepository(session).update_status(
                ticket_id=ticket_id,
                status=request.status,
                agent_response=request.agent_response,
            )