"""
app/nodes/argument_validation_node.py

Purpose:
--------
Validate that all required arguments for the selected tool are present
in state.extracted_arguments before execution is attempted.

This node is the gatekeeper between language understanding and business action.

Responsibilities:
-----------------
- Read state.tool_decision (which tool was selected).
- Read state.extracted_arguments (what was extracted from the message).
- Check that all required arguments for the selected tool are present.
- Write state.missing_arguments (list of missing field names, if any).
- Write state.needs_clarification (True if any required argument is missing).
- Return updated state.

This module DOES NOT:
---------------------
- Execute tools (tool_executor_node's responsibility).
- Extract information from messages (argument_extraction_node's responsibility).
- Generate customer-facing responses (response_node's responsibility).
- Decide which tool to use (llm_decision_node's responsibility).
- Validate argument values beyond presence (e.g., format, range).

Architecture position:
----------------------
    llm_decision_node           → Reason
          ↓
    argument_extraction_node    → Extract
          ↓
    argument_validation_node    → Validate   ← this file
          ↓
    tool_executor_node          → Act
          ↓
    response_node               → Respond

Why validation belongs here and not in the executor:
-----------------------------------------------------
Without a validation node, every tool or executor branch must defensively
check for None arguments:

    if ticket_id is None:
        # handle missing argument

This scatters validation logic across tools and forces tools to handle
cases that aren't their responsibility. Tools should assume arguments
are present and valid — that is a cleaner contract.

The validation node enforces this contract at the boundary between
extraction and execution. If arguments are missing, execution is skipped
entirely, and the customer receives a targeted clarification request.

Why validation belongs here and not in the extraction node:
-----------------------------------------------------------
The extraction node answers: "What information exists in this message?"
It should not know which tools require which arguments — that would
couple it to tool signatures.

The validation node answers: "Does the selected tool have what it needs?"
It reads both tool_decision (which tool) and extracted_arguments (what
was found) to make this determination. Two inputs, one responsibility.

Required Arguments Registry:
-----------------------------
Maps tool_name → list of required argument names.

    _REQUIRED_ARGUMENTS = {
        "create_ticket_tool": [],           # arguments built from state, always present
        "get_ticket_tool":    ["ticket_id"],# must be extracted from message
    }

no_tool has no entry — validation is skipped for it.

Adding a new tool:
    1. Add the tool's required argument names to _REQUIRED_ARGUMENTS.
    2. No other changes needed.

Why create_ticket_tool has no required arguments:
-------------------------------------------------
Its arguments (customer_id, issue) come from state fields always present
in AgentState, not from extraction. They cannot be missing.
"""

import logging

from app.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required Arguments Registry
#
# Maps tool_name → list of argument names that must exist in
# state.extracted_arguments before execution is allowed.
#
# Only include tools whose arguments come from extraction.
# Tools whose arguments come entirely from state fields (customer_id,
# message) don't need extraction-based validation.
# ---------------------------------------------------------------------------
_REQUIRED_ARGUMENTS: dict[str, list[str]] = {
    "create_ticket_tool": [],            # customer_id + message always in state
    "get_ticket_tool":    ["ticket_id"], # must be extracted from natural language
}


# ---------------------------------------------------------------------------
# Node: argument_validation_node
#
# LangGraph node contract: (state: AgentState) -> AgentState
#
# Reads:  state.tool_decision, state.extracted_arguments
# Writes: state.missing_arguments, state.needs_clarification
#
# Does NOT write: state.response (response_node owns customer communication)
# ---------------------------------------------------------------------------

def argument_validation_node(state: AgentState) -> AgentState:
    """
    Validate that required arguments for the selected tool are present.

    If any required argument is missing:
        state.needs_clarification = True
        state.missing_arguments   = [list of missing field names]

    The executor checks state.needs_clarification and skips execution.
    The response node checks state.needs_clarification and produces a
    targeted clarification prompt instead of a result response.

    For no_tool or tools not in the registry:
        Validation passes (nothing to validate).

    Args:
        state: Current AgentState.

    Returns:
        Updated AgentState with validation results populated.
    """

    # No decision → nothing to validate.
    if state.tool_decision is None or state.tool_decision.is_no_tool():
        logger.debug("argument_validation_node: no_tool or no decision — skipping.")
        return state

    tool_name = state.tool_decision.tool_name
    required  = _REQUIRED_ARGUMENTS.get(tool_name, [])

    # No requirements registered for this tool → pass through.
    if not required:
        logger.debug(
            "argument_validation_node: no required args for '%s' — passing.",
            tool_name,
        )
        return state

    logger.info(
        "argument_validation_node started",
        extra={"customer_id": state.customer_id, "tool_name": tool_name},
    )

    # Check each required argument against extracted_arguments.
    missing: list[str] = []

    for arg in required:
        value = (
            state.extracted_arguments.get(arg)
            if state.extracted_arguments is not None
            else None
        )
        if value is None:
            missing.append(arg)

    if missing:
        state.needs_clarification = True
        state.missing_arguments   = missing
        logger.info(
            "argument_validation_node: missing required args %s for tool '%s'.",
            missing,
            tool_name,
            extra={"customer_id": state.customer_id},
        )
    else:
        # All required arguments are present — execution can proceed.
        state.needs_clarification = False
        state.missing_arguments   = [] 
        logger.info(
            "argument_validation_node: all required args present for '%s'.",
            tool_name,
            extra={"customer_id": state.customer_id},
        )

    return state