"""
app/nodes/tool_executor_node.py

Purpose:
--------
Execute the tool selected by the LLM decision node and store the
raw result as an observation in AgentState.

Responsibilities:
-----------------
- Read state.tool_decision.
- Look up the ToolSpec in TOOL_REGISTRY.
- Build arguments via spec.argument_builder(state).
- Execute spec.tool_fn(**arguments).
- Write state.tool_used and state.tool_result.
- Return updated state.

This module DOES NOT:
---------------------
- Define tool functions, argument builders, or response builders
  (tool_registry.py owns all of that via ToolSpec).
- Generate customer-facing responses.
- Validate argument presence (argument_validation_node's responsibility).
- Call the LLM.

Architecture change from Milestone 7:
--------------------------------------
Before: _TOOL_REGISTRY and _ARGUMENT_BUILDERS lived in this file.
After:  spec.tool_fn and spec.argument_builder are read from TOOL_REGISTRY.

The execution logic is unchanged. Only the source of truth moved.
Adding a new tool no longer requires editing this file.

Observation pattern:
--------------------
state.tool_result stores the full raw object returned by the tool.
Consumers (response_node, eval_node, audit_node) extract what they need.
The executor never flattens or interprets the result.
"""

import logging

from app.schemas.agent_state import AgentState
from app.tools.tool_registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)


def tool_executor_node(state: AgentState) -> AgentState:
    """
    Execute the selected tool and store the raw result as an observation.

    Skip conditions (return state unchanged):
        1. tool_decision is None      — graph wiring error
        2. is_no_tool() is True       — LLM chose no action
        3. needs_clarification True   — required arguments missing

    On unknown tool_name or execution failure:
        Logs the error, leaves tool_result as None.
        response_node detects None and handles gracefully.
    """

    if state.tool_decision is None:
        logger.error(
            "tool_executor_node called with no tool_decision. "
            "Check graph wiring — llm_decision_node must run first.",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    assert state.tool_decision is not None  # Pylance narrowing

    if state.tool_decision.is_no_tool():
        logger.info(
            "tool_executor_node: no_tool — skipping execution.",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    if state.needs_clarification:
        logger.info(
            "tool_executor_node: needs_clarification=True — skipping. Missing: %s",
            state.missing_arguments,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    tool_name = state.tool_decision.tool_name
    spec      = TOOL_REGISTRY.get(tool_name)

    if spec is None:
        logger.error(
            "tool_executor_node: tool '%s' not found in TOOL_REGISTRY.",
            tool_name,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )
        return state

    logger.info(
        "tool_executor_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_name
        },
    )

    try:
        arguments = spec.argument_builder(state)
        result    = spec.tool_fn(**arguments)

        state.tool_used   = tool_name
        state.tool_result = result

        logger.info(
            "tool_executor_node completed",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
                "tool_name": tool_name,
                "tool_result": repr(result)
            },
        )

    except Exception as e:
        logger.error(
            "tool_executor_node: tool '%s' raised %s: %s",
            tool_name, type(e).__name__, e,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id
            },
        )

    return state