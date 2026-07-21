"""
app/nodes/response_node.py

Purpose:
--------
Convert the tool execution result (observation) into a customer-facing
response and write it to AgentState.

Responsibilities:
-----------------
- Read state.tool_decision, state.tool_used, state.tool_result,
  state.needs_clarification, state.missing_arguments.
- Generate a deterministic customer-facing response.
- Write state.response and state.ticket_id.
- Return updated state.

This module DOES NOT:
---------------------
- Define response builders (tool_registry.py owns those via ToolSpec).
- Execute tools or call the LLM.
- Own business rules about ticket creation or status.
- Mutate state.tool_result.

Architecture change from Milestone 7:
--------------------------------------
Before: _RESPONSE_BUILDERS dict lived in this file alongside builder functions.
After:  spec.response_builder is read from TOOL_REGISTRY.

Response builders and clarification prompts are the only things still
owned here — builders moved to tool_registry.py, but clarification
prompt text stays here because customer communication is this node's
responsibility regardless of the registry.
"""

import logging
from typing import Any

from app.schemas.agent_state import AgentState
from app.tools.tool_registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clarification Prompts
#
# Maps missing argument names to targeted customer-facing prompts.
# Owned here (not in validation node) because customer communication
# is always response_node's responsibility.
# ---------------------------------------------------------------------------
_CLARIFICATION_PROMPTS: dict[str, str] = {
    "ticket_id": (
        "Could you please provide your ticket ID? "
        "It looks like TICKET- followed by letters and numbers (e.g. TICKET-123)."
    ),
    "order_id": (
        "Could you please provide your order ID so I can look that up for you?"
    ),
}

_DEFAULT_CLARIFICATION = (
    "Could you provide more details so I can assist you? "
    "I'm missing some information needed to complete your request."
)

_NO_TOOL_RESPONSE = (
    "Thank you for reaching out. "
    "Could you provide more details about your issue so I can assist you better?"
)

_FALLBACK_RESPONSE = (
    "We're unable to process your request automatically right now.\n\n"
    "Your request has been escalated to a support specialist who will "
    "contact you shortly to resolve this."
)


def response_node(state: AgentState) -> AgentState:
    """
    Generate a customer-facing response from the agent's observation.

    Cases handled in order:
        1.  no_tool            → ask for more details
        1b. needs_clarification → targeted clarification prompt
        2.  tool_used is None  → system failure → escalate
        3.  spec not found     → developer oversight → escalate
        4.  builder returns "" → tool-specific failure → escalate
        5.  success            → builder produces response
    """

    logger.info("response_node started", extra={
        "request_id": state.request_id,
        "customer_id": state.customer_id
    })

    # Case 1: no_tool
    if state.tool_decision is None or state.tool_decision.is_no_tool():
        state.response = _NO_TOOL_RESPONSE
        logger.info("response_node: no_tool path.")
        return state

    # Case 1b: clarification required
    if state.needs_clarification and state.missing_arguments:
        first_missing  = state.missing_arguments[0]
        state.response = _CLARIFICATION_PROMPTS.get(first_missing, _DEFAULT_CLARIFICATION)
        logger.info(
            "response_node: needs_clarification=True. Missing: %s",
            state.missing_arguments,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    tool_name = state.tool_used

    # Case 2: executor skipped but not due to no_tool or clarification
    if tool_name is None:
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        logger.warning(
            "response_node: tool_used is None — escalating.",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    # Case 3: look up ToolSpec
    spec = TOOL_REGISTRY.get(tool_name)

    if spec is None:
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        logger.error(
            "response_node: tool '%s' not found in TOOL_REGISTRY — escalating.",
            tool_name,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    # Case 4/5: call the response builder
    # Pass tool_result directly — including None.
    # Each builder owns the semantics of None for its specific tool.
    state.response = spec.response_builder(state.tool_result)

    if not state.response:
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        logger.error(
            "response_node: builder for '%s' returned empty — escalating.",
            tool_name,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    # Extract ticket_id for the API layer
    if hasattr(state.tool_result, "ticket_id"):
        state.ticket_id = state.tool_result.ticket_id  # type: ignore

    logger.info(
        "response_node completed",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_name,
            "ticket_id": state.ticket_id
        },
    )

    return state