"""
app/tools/escalation_tools.py

Purpose:
--------
Expose escalation capabilities to agents as thin adapters.
Mirrors ticket_tools.py in structure and philosophy.

Thin adapter: receives structured inputs, calls EscalationService,
returns EscalationResponse. No business logic.
"""

from app.schemas.escalation import CreateEscalationRequest, EscalationQueue, EscalationResponse
from app.services.escalation_service import EscalationService

_escalation_service = EscalationService()


def create_escalation_tool(
    customer_id: str,
    reason:      str,
    queue:       str = "general",
) -> EscalationResponse:
    """
    Create a human escalation for a customer issue.

    Args:
        customer_id: The customer requiring human assistance.
        reason:      Why automation cannot handle this request.
        queue:       Which team receives the escalation ("general",
                     "legal", "safety", "billing").

    Returns:
        EscalationResponse with escalation_id and status=OPEN.
    """
    request = CreateEscalationRequest(
        customer_id=customer_id,
        reason=reason,
        queue=EscalationQueue(queue),
    )
    return _escalation_service.create_escalation(request)


def get_escalation_tool(escalation_id: str) -> EscalationResponse | None:
    """
    Retrieve an existing escalation by ID.

    Returns:
        EscalationResponse if found, None otherwise.
    """
    return _escalation_service.get_escalation(escalation_id)