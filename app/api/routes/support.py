"""
app/api/routes/support.py

Purpose:
--------
FastAPI routes for the customer support platform.

Responsibilities:
-----------------
- Define HTTP endpoints for customer message processing.
- Use FastAPI dependency injection for all services.
- Translate AgentState into HTTP responses.
- Handle input validation via Pydantic request schemas.

This module DOES NOT:
---------------------
- Contain business logic.
- Call services or repositories directly (via DI only).
- Know about graph internals, routing logic, or tool selection.

Endpoints:
----------
    POST /support/message   → process a customer message end-to-end
    GET  /support/tickets/{ticket_id} → retrieve a ticket by ID
    GET  /health            → service health check
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_router_service, get_ticket_service
from app.services.router_service import RouterService
from app.services.ticket_service import TicketService

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Schemas
#
# Separate from AgentState — API contracts should not expose internal state.
# These schemas define what the HTTP client sends and receives.
# ---------------------------------------------------------------------------

class MessageRequest(BaseModel):
    """Incoming customer message."""
    customer_id: str
    message:     str


class MessageResponse(BaseModel):
    """
    Response returned to the client after processing.
    Extracts only the fields relevant to the external contract.
    """
    request_id:          str | None
    customer_id:         str
    response:            str
    ticket_id:           str | None = None
    agent_name:          str | None = None
    needs_human:         bool = False
    needs_clarification: bool = False


class TicketResponse(BaseModel):
    """Ticket details returned by GET /tickets/{ticket_id}."""
    ticket_id:   str
    customer_id: str
    issue:       str
    status:      str


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Service liveness check."""
    return HealthResponse(status="ok")


@router.post("/support/message", response_model=MessageResponse, tags=["Support"])
def process_message(
    request:        MessageRequest,
    router_service: RouterService = Depends(get_router_service),
) -> MessageResponse:
    """
    Process a customer support message end-to-end.

    Routes the message through the multi-agent pipeline and returns
    the agent's response along with relevant metadata.

    The API layer does not know which agent handled the request,
    which tool was used, or how memory was loaded — it only sees
    the final AgentState fields it needs to build the response.
    """
    state = router_service.run(
        customer_id=request.customer_id,
        message=request.message,
    )

    return MessageResponse(
        request_id=state.request_id,
        customer_id=state.customer_id,
        response=state.response or "I was unable to process your request.",
        ticket_id=state.ticket_id,
        agent_name=(
            state.routing_decision.agent_name
            if state.routing_decision else None
        ),
        needs_human=state.needs_human,
        needs_clarification=state.needs_clarification,
    )


@router.get(
    "/support/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Support"],
)
def get_ticket(
    ticket_id:      str,
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Retrieve a support ticket by ID.

    Returns 404 if the ticket does not exist.
    This endpoint is separate from the agent pipeline —
    it's a direct service call for dashboard or admin use.
    """
    ticket = ticket_service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        customer_id=ticket.customer_id,
        issue=ticket.issue,
        status=ticket.status.value,
    )