"""
app/services/escalation_service.py

Purpose:
--------
Orchestrates escalation lifecycle. Mirrors TicketService exactly.
Delegates persistence to EscalationRepository via get_session().
Does not know SQLAlchemy exists.
"""

import uuid

from app.database.connection import get_session
from app.repositories.escalation_repository import EscalationRepository
from app.schemas.escalation import (
    CreateEscalationRequest,
    EscalationQueue,
    EscalationResponse,
)


class EscalationService:

    def create_escalation(
        self, request: CreateEscalationRequest
    ) -> EscalationResponse:
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        with get_session() as session:
            return EscalationRepository(session).create(
                escalation_id=escalation_id,
                customer_id=request.customer_id,
                reason=request.reason,
                queue=request.queue,
            )

    def get_escalation(self, escalation_id: str) -> EscalationResponse | None:
        with get_session() as session:
            return EscalationRepository(session).get(escalation_id)


escalation_service = EscalationService()