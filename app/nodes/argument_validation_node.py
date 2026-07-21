"""
app/nodes/argument_validation_node.py

Purpose:
--------
Validate that all required arguments for the selected tool are present
in state.extracted_arguments before execution is attempted.

Responsibilities:
-----------------
- Read state.tool_decision (which tool was selected).
- Look up the tool's ToolSpec in TOOL_REGISTRY.
- Check that all required_arguments are present in state.extracted_arguments.
- Write state.missing_arguments and state.needs_clarification.
- Return updated state.

This module DOES NOT:
---------------------
- Define required arguments per tool (tool_registry.py owns that via ToolSpec).
- Execute tools or generate responses.
- Extract information from messages.

Architecture change from Milestone 7:
--------------------------------------
Before: _REQUIRED_ARGUMENTS dict lived inside this file.
After:  spec.required_arguments is read from TOOL_REGISTRY.

The validation logic is unchanged. Only the source of truth moved.
Adding a new tool no longer requires editing this file.
"""

import logging

from app.schemas.agent_state import AgentState
from app.tools.tool_registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)


def argument_validation_node(state: AgentState) -> AgentState:
    """
    Validate required arguments for the selected tool are present.

    Reads spec.required_arguments from TOOL_REGISTRY[tool_name].
    If any required argument is absent from state.extracted_arguments:
        state.needs_clarification = True
        state.missing_arguments   = [missing field names]

    For no_tool or unregistered tools: passes through unchanged.
    """

    if state.tool_decision is None or state.tool_decision.is_no_tool():
        logger.debug("argument_validation_node: no_tool or no decision — skipping.")
        return state

    tool_name = state.tool_decision.tool_name
    spec      = TOOL_REGISTRY.get(tool_name)

    if spec is None or not spec.required_arguments:
        logger.debug(
            "argument_validation_node: no required args for '%s' — passing.",
            tool_name,
        )
        return state

    logger.info(
        "argument_validation_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_name
        },
    )

    missing: list[str] = [
        arg for arg in spec.required_arguments
        if (
            state.extracted_arguments is None
            or state.extracted_arguments.get(arg) is None
        )
    ]

    if missing:
        state.needs_clarification = True
        state.missing_arguments   = missing
        logger.info(
            "argument_validation_node: missing required args %s for tool '%s'.",
            missing, tool_name,
            extra={"customer_id": state.customer_id},
        )
    else:
        state.needs_clarification = False
        state.missing_arguments   = []
        logger.info(
            "argument_validation_node: all required args present for '%s'.",
            tool_name,
            extra={"customer_id": state.customer_id},
        )

    return state