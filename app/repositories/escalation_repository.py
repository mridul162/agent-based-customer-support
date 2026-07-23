"""
app/repositories/escalation_repository.py

Purpose:
--------
Data access layer for escalations. Mirrors TicketRepository exactly.
The only layer that knows about the Escalation ORM model.

Transaction ownership: get_session() in the service layer.
This repository never calls commit() or rollback().
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.escalation_model import Escalation
from app.schemas.escalation import EscalationQueue, EscalationResponse, EscalationStatus


class EscalationRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        escalation_id: str,
        customer_id:   str,
        reason:        str,
        queue:         EscalationQueue,
    ) -> EscalationResponse:
        escalation = Escalation(
            escalation_id=escalation_id,
            customer_id=customer_id,
            reason=reason,
            queue=queue,
            status=EscalationStatus.OPEN,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(escalation)
        self._session.flush()
        self._session.refresh(escalation)
        return self._to_response(escalation)

    def get(self, escalation_id: str) -> EscalationResponse | None:
        escalation = self._session.get(Escalation, escalation_id)
        if escalation is None:
            return None
        return self._to_response(escalation)

    @staticmethod
    def _to_response(escalation: Escalation) -> EscalationResponse:
        return EscalationResponse(
            escalation_id=escalation.escalation_id,
            customer_id=escalation.customer_id,
            reason=escalation.reason,
            queue=escalation.queue,
            status=escalation.status,
            created_at=escalation.created_at,
        )