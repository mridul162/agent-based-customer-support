"""
app/nodes/response_node.py

Purpose:
--------
Convert the tool execution result (observation) into a customer-facing
response and write it to AgentState. This is the final stage of the
agent loop for Milestone 4.

Responsibilities:
-----------------
- Read state.tool_result and state.tool_decision.
- Generate a deterministic customer-facing response string.
- Write state.response.
- Write state.ticket_id (extracted from tool_result for convenience).
- Return updated state.

This module DOES NOT:
---------------------
- Execute tools (tool_executor_node's responsibility).
- Make LLM calls (deliberate design decision — see below).
- Decide which tool was used (reads state.tool_used for that).
- Own business rules about ticket creation or status.
- Modify state.tool_result (consumers read, never modify the observation).

Design Decision — Deterministic vs LLM Response Generation:
------------------------------------------------------------
Option A (chosen): deterministic f-string responses.
Option B (deferred): LLM-generated natural language responses.

Why Option A now?
    The current problem is simple: turn a TicketResponse into a
    confirmation message. The content is fully determined by the tool
    result — ticket ID, status, a fixed support message.
    No ambiguity. No creativity required. An LLM adds nothing here
    except latency, cost, and a new failure surface.

Why Option B later?
    When responses need to summarize complex tool results, match the
    customer's tone, or handle nuanced multi-turn context, an LLM
    becomes genuinely useful. That's a real problem worth solving.
    Today's problem isn't.

Upgrade path (Option A → Option B):
    This node's contract is: read state → write state.response.
    To add LLM generation later, replace the _build_response() logic
    with an LLM call. The node's signature and the graph wiring
    don't change. The rest of the system doesn't know or care.

Architecture position in the ReAct loop:
-----------------------------------------
    State
      ↓
    LLM Decision Node   → Reason
      ↓
    Tool Executor Node  → Act + Observe
      ↓
    Response Node       → Respond         ← this file
      ↓
    Final AgentState
"""

import logging
from typing import Any

from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import NO_TOOL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response Builders
#
# Maps tool_name → a function that builds the customer response string
# from the raw tool result.
#
# Why a registry pattern here too?
#     Consistent with _TOOL_REGISTRY and _ARGUMENT_BUILDERS in the executor.
#     Adding a new tool means adding one entry here — response_node never
#     changes. Each builder is independently readable and testable.
#
# Each builder receives the full tool_result object (not just ticket_id),
# so future builders can access any field without this node needing to change.
# ---------------------------------------------------------------------------

def _build_ticket_response(tool_result: Any) -> str:
    """Build a customer confirmation message from a TicketResponse."""
    return (
        f"Your support ticket has been created successfully.\n\n"
        f"Ticket ID: {tool_result.ticket_id}\n\n"
        f"Our team will review your request and contact you shortly."
    )


_RESPONSE_BUILDERS: dict[str, Any] = {
    "create_ticket_tool": _build_ticket_response,
}

# Response used when the LLM chose no_tool — no action was needed.
_NO_TOOL_RESPONSE = (
    "Thank you for reaching out. "
    "Could you provide more details about your issue so I can assist you better?"
)

# Response used when tool execution failed (tool_result is None but a tool was selected).
# Sets state.needs_human = True so the failure becomes a workflow event,
# not just an error message. Ownership is assigned; the customer is not left stuck.
_FALLBACK_RESPONSE = (
    "We're unable to process your request automatically right now.\n\n"
    "Your request has been escalated to a support specialist who will "
    "contact you shortly to resolve this."
)


# ---------------------------------------------------------------------------
# Node: response_node
#
# LangGraph node contract: (state: AgentState) -> AgentState
#
# Reads:  state.tool_decision, state.tool_used, state.tool_result
# Writes: state.response, state.ticket_id
#
# Does NOT modify: state.tool_result (observation is read-only by consumers)
# ---------------------------------------------------------------------------

def response_node(state: AgentState) -> AgentState:
    """
    Generate a customer-facing response from the agent's observation.

    Three cases handled:
        1. no_tool:        LLM chose no action — ask for more details.
        2. tool succeeded: Build response from tool_result via registry.
        3. tool failed:    tool_result is None — return honest fallback.

    ticket_id is extracted here (not in the executor) because:
        - The executor's job is to store the observation, not extract fields.
        - This node is the first consumer with a reason to need ticket_id
          (for the response text and for the API layer to return).
        - Other consumers (eval, audit) will extract what they need from
          state.tool_result directly.

    Args:
        state: Current AgentState. Reads tool_decision, tool_used, tool_result.

    Returns:
        Updated AgentState with response and ticket_id populated.
    """

    logger.info(
        "response_node started",
        extra={"customer_id": state.customer_id},
    )

    # Case 1: LLM chose no_tool — no ticket was created, no result to read.
    # The `or` short-circuits: if tool_decision is None, is_no_tool() is never called.
    # Pylance understands this pattern — no separate assert needed here.
    if state.tool_decision is None or state.tool_decision.is_no_tool():
        state.response = _NO_TOOL_RESPONSE
        logger.info("response_node: no_tool path — returning clarification response.")
        return state

    tool_name = state.tool_used

    # Case 2: tool was selected but execution failed (tool_result is None).
    # Failure becomes a workflow state change, not just an error message.
    # state.needs_human = True assigns ownership: a human agent takes over.
    # The customer is not left with "please try again" and no path forward.
    if tool_name is None or state.tool_result is None:
        state.needs_human = True
        state.response = _FALLBACK_RESPONSE
        logger.warning(
            "response_node: tool_result is None for tool '%s' — "
            "escalating to human agent (needs_human=True).",
            tool_name,
            extra={"customer_id": state.customer_id},
        )
        return state

    # Case 3: tool succeeded — build response from the observation.
    builder = _RESPONSE_BUILDERS.get(tool_name)

    if builder is None:
        # Tool ran successfully but no response builder is registered.
        # Developer oversight — escalate to human so the customer isn't stuck.
        state.needs_human = True
        state.response = _FALLBACK_RESPONSE
        logger.error(
            "response_node: no response builder registered for tool '%s'. "
            "Add an entry to _RESPONSE_BUILDERS. Escalating to human agent.",
            tool_name,
            extra={"customer_id": state.customer_id},
        )
        return state

    state.response = builder(state.tool_result)

    # Extract ticket_id from the tool result for the API layer.
    # The API response needs ticket_id as a top-level field (AgentResponse.ticket_id).
    # This is the appropriate place to extract it: this node is the first
    # consumer that needs it, and it reads from the preserved observation.
    if hasattr(state.tool_result, "ticket_id"):
        state.ticket_id = state.tool_result.ticket_id

    logger.info(
        "response_node completed",
        extra={
            "tool_name":  tool_name,
            "ticket_id":  state.ticket_id,
        },
    )

    return state