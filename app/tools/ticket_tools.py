"""
app/tools/ticket_tools.py

Responsibility:
    - Expose TicketService capabilities to the agent layer.
    - Act as thin adapters: translate agent inputs → service calls → structured outputs.
    - Bridge the gap between LLM-world (intent) and application-world (business systems).

Should NOT:
    - Contain business rules (status logic, lifecycle rules, validation).
    - Access the database directly.
    - Parse or interpret raw customer messages.
    - Become mini-agents with branching decision logic.

Mental model:
    Agent Intent → Tool (thin adapter) → TicketService (business logic) → Storage
"""

from app.schemas.ticket import (
    CreateTicketRequest,
    UpdateTicketRequest,
    TicketResponse,
    TicketStatus,
)

from app.services.ticket_service import TicketService


# ---------------------------------------------------------------------------
# Module-level service instance.
#
# Why here and not injected?
# For Milestone 1 (in-memory storage), a module-level instance is acceptable.
# All tools in this file share the same instance, so state is consistent
# within a single process run.
#
# Future improvement (noted, not premature):
# When we move to PostgreSQL and introduce dependency injection,
# TicketService will receive a DB session and be injected per-request.
# At that point, tools will receive the service instance rather than
# constructing it themselves.
# ---------------------------------------------------------------------------
_ticket_service = TicketService()


def create_ticket_tool(customer_id: str, issue: str) -> TicketResponse:
    """
    Expose ticket creation capability to the agent.

    The tool's job:
        1. Accept structured inputs from the agent.
        2. Construct the request schema.
        3. Delegate to TicketService.
        4. Return the typed result.

    Business rules (initial status = OPEN, ID generation) live in
    TicketService, not here.

    Args:
        customer_id: The ID of the customer submitting the ticket.
        issue:       The customer's support issue, as understood by the agent.

    Returns:
        TicketResponse: The created ticket with ID, status, and metadata.
    """

    request = CreateTicketRequest(
        customer_id=customer_id,
        issue=issue,
    )

    return _ticket_service.create_ticket(request)


def get_ticket_tool(ticket_id: str) -> TicketResponse | None:
    """
    Expose ticket retrieval capability to the agent.

    Returns None if the ticket does not exist.
    The agent (or API layer) is responsible for deciding how to
    handle a missing ticket — that decision does not belong here.

    Args:
        ticket_id: The unique identifier of the ticket to retrieve.

    Returns:
        TicketResponse if found, None otherwise.
    """

    return _ticket_service.get_ticket(ticket_id)


def list_tickets_tool() -> list[TicketResponse]:
    """
    Expose ticket listing capability to the agent.

    Thin pass-through. No filtering, sorting, or pagination logic here.
    If those are needed later, they belong in TicketService, not in this tool.

    Returns:
        List of all TicketResponse objects. Empty list if none exist.
    """

    return _ticket_service.list_tickets()


def update_ticket_tool(
    ticket_id: str,
    status: TicketStatus | None = None,
    agent_response: str | None = None,
) -> TicketResponse | None:
    """
    Expose ticket update capability to the agent.

    Accepts individual fields rather than a raw UpdateTicketRequest,
    because the agent reasons about parameters one at a time, not as
    schema objects.

    This is a valid and intentional exception to "zero logic in tools":
    the tool performs lightweight input adaptation (individual args →
    UpdateTicketRequest schema) before delegating to the service.
    This translation is interface adaptation, not business logic.

    What this tool does NOT decide:
        - Whether a status transition is valid (e.g., RESOLVED → OPEN).
        - What the agent_response should say.
        - Whether the ticket should be escalated.
    Those are business rules that belong in TicketService.

    Args:
        ticket_id:      The ticket to update.
        status:         New status, if being changed. None = leave unchanged.
        agent_response: Agent's response text, if being set. None = leave unchanged.

    Returns:
        Updated TicketResponse if ticket exists, None otherwise.
    """

    request = UpdateTicketRequest(
        status=status,
        agent_response=agent_response,
    )

    return _ticket_service.update_ticket(ticket_id, request)