"""
app/services/router_service.py

Purpose:
--------
Single application entry point for processing customer messages.

Wraps router_graph.invoke() with:
    - request_id generation (for tracing and observability)
    - structured logging with request context
    - clean AgentState construction
    - typed return value

Responsibilities:
-----------------
- Generate a unique request_id per invocation.
- Build the initial AgentState dict for the graph.
- Invoke router_graph and return the final AgentState.
- Log request start and completion with full context.

This service DOES NOT:
----------------------
- Know about graph internals, nodes, or routing logic.
- Call tools or services directly.
- Handle HTTP — that's the API layer's responsibility.

Why a RouterService instead of calling router_graph.invoke() directly?
----------------------------------------------------------------------
Calling router_graph.invoke() directly from API routes means:
    - request_id generation is duplicated across routes
    - structured logging setup is duplicated
    - the graph becomes hard to swap in tests
    - future middleware (rate limiting, auth, observability) has no home

RouterService is the stable interface between the HTTP layer and the
graph layer. Swapping the graph (or adding middleware) touches one file.

Architecture:
-------------
    FastAPI Route
          ↓
    RouterService.run()    ← this file
          ↓
    router_graph.invoke()
          ↓
    AgentState (final)
"""

import logging
import uuid

from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)


class RouterService:
    """
    Application-level entry point for customer message processing.

    Each call to run() represents one complete request lifecycle:
        receive → route → execute → respond → return
    """

    def run(
        self,
        customer_id: str,
        message:     str,
    ) -> AgentState:
        """
        Process a customer message through the full multi-agent pipeline.

        Generates a unique request_id for tracing, then invokes the
        router graph and returns the fully populated AgentState.

        Args:
            customer_id: The customer's unique identifier.
            message:     The customer's raw message text.

        Returns:
            Final AgentState after all nodes have executed.
            Always contains at minimum: response, routing_decision.
        """
        request_id = str(uuid.uuid4())

        logger.info(
            "RouterService: request started",
            extra={
                "request_id":  request_id,
                "customer_id": customer_id,
                "message_len": len(message),
            },
        )

        result = router_graph.invoke({
            "customer_id": customer_id,
            "message":     message,
            "request_id":  request_id,
        })

        state = AgentState(**result)

        logger.info(
            "RouterService: request completed",
            extra={
                "request_id":    request_id,
                "customer_id":   customer_id,
                "agent_name":    state.routing_decision.agent_name if state.routing_decision else None,
                "tool_used":     state.tool_used,
                "ticket_id":     state.ticket_id,
                "needs_human":   state.needs_human,
                "needs_clarification": state.needs_clarification,
            },
        )

        return state