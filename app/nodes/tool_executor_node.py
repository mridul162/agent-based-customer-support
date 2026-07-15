"""
app/nodes/tool_executor_node.py

Purpose:
--------
Execute the tool selected by the LLM decision node and store the
raw result as an observation in AgentState.

Responsibilities:
-----------------
- Read state.tool_decision (set by llm_decision_node).
- Look up the tool in _TOOL_REGISTRY by tool_name.
- Build tool arguments from state (Design B: executor owns argument construction).
- Execute the tool.
- Write state.tool_used and state.tool_result (the observation).
- Return updated state.

This module DOES NOT:
---------------------
- Decide which tool to call (llm_decision_node's responsibility).
- Generate customer-facing response text (response node's responsibility).
- Modify ticket status or business data beyond what the tool itself does.
- Build prompts or call the LLM.
- Flatten tool results into individual state fields (consumers do that).

Architecture Philosophy:
------------------------
The agent loop this node completes:

    State
      ↓
    LLM Decision Node   → answers: "What should happen?"
      ↓
    Tool Executor Node  → answers: "Execute it. What was observed?"  ← this file
      ↓
    Response Node       → answers: "How do we communicate this?"

This is the ReAct pattern (Reason → Act → Observe → Respond),
arrived at organically through architectural decisions rather than
introduced as a named framework.

Tool Registry:
--------------
A dict mapping tool_name strings to callable functions.

    _TOOL_REGISTRY = {
        "create_ticket_tool": create_ticket_tool,
    }

Why a registry instead of if/elif?
    - Adding a new tool = one new entry. The executor never changes.
    - The LLM's tool_name string maps directly to a callable.
    - Testable: the registry can be inspected to verify registered tools.
    - Mirrors how production tool-calling systems work (OpenAI function
      registry, LangChain tool lists, LangGraph ToolNode).

Design B — executor builds arguments:
--------------------------------------
Today's tools (create_ticket_tool) need customer_id and issue.
Both already exist in state — the LLM did not derive them.

Executor builds:
    arguments = _ARGUMENT_BUILDERS[tool_name](state)

rather than reading from state.tool_decision.arguments,
because the LLM copying state values into arguments is wasted
tokens and an extra failure surface (Design B from architecture review).

When tools need LLM-derived arguments (order_id, reason, etc.),
those values will be added to state.tool_decision.arguments by the
decision node (Design A), and the argument builder will read them.
Both patterns coexist cleanly in this structure.

Observation pattern:
--------------------
state.tool_result stores the raw object returned by the tool.
This is the observation. Downstream nodes extract what they need:

    response_node reads:  state.tool_result.ticket_id
    eval_node reads:      state.tool_result.status
    audit_node reads:     state.tool_result  (full object)

The executor cannot predict what consumers will need.
Flattening prematurely discards information. Preserve and let consumers decide.
"""

import logging
from typing import Any, Callable

from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import NO_TOOL
from app.tools.ticket_tools import create_ticket_tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias for tool callables.
# Every registered tool takes keyword arguments and returns Any.
# ---------------------------------------------------------------------------
ToolFn = Callable[..., Any]

# ---------------------------------------------------------------------------
# Argument Builders
#
# Maps tool_name → a function that builds that tool's keyword arguments
# from AgentState.
#
# Why separate from _TOOL_REGISTRY?
#     Argument construction is a different concern from tool execution.
#     A tool's signature may change without the tool's registry entry
#     changing, and vice versa. Separating them keeps each dict focused.
#
# Design B in practice:
#     The builder reads directly from state, not from
#     state.tool_decision.arguments. The LLM is not asked to re-state
#     values that already exist in state.
#
# Future Design A extension:
#     When a tool needs LLM-derived values, the builder reads them from
#     state.tool_decision.arguments:
#         "order_id": state.tool_decision.arguments.get("order_id")
#     Both patterns are addable here without changing the executor logic.
# ---------------------------------------------------------------------------
_ARGUMENT_BUILDERS: dict[str, Callable[[AgentState], dict[str, Any]]] = {
    "create_ticket_tool": lambda state: {
        "customer_id": state.customer_id,
        "issue":       state.message,
    },
}

# ---------------------------------------------------------------------------
# Tool Registry
#
# Maps tool_name strings to callable tool functions.
# The LLM's tool_name in ToolDecision must match a key here exactly.
#
# Adding a new tool:
#     1. Import the tool function.
#     2. Add one entry to _TOOL_REGISTRY.
#     3. Add one entry to _ARGUMENT_BUILDERS.
#     The executor node never changes.
# ---------------------------------------------------------------------------
_TOOL_REGISTRY: dict[str, ToolFn] = {
    "create_ticket_tool": create_ticket_tool,
}


# ---------------------------------------------------------------------------
# Node: tool_executor_node
#
# LangGraph node contract: (state: AgentState) -> AgentState
#
# Reads:  state.tool_decision
# Writes: state.tool_used, state.tool_result
#
# Does NOT write: state.response (response node's responsibility)
# ---------------------------------------------------------------------------

def tool_executor_node(state: AgentState) -> AgentState:
    """
    Execute the tool selected by the LLM and store the raw result.

    Workflow:
        1. Check for no_tool — skip execution if the LLM chose no action.
        2. Look up the tool in _TOOL_REGISTRY.
        3. Build arguments via _ARGUMENT_BUILDERS.
        4. Execute the tool.
        5. Write state.tool_used and state.tool_result.

    On unknown tool_name:
        Logs an error and leaves state.tool_result as None.
        This surfaces as a missing response downstream rather than a crash.
        A future improvement is setting state.needs_human = True here.

    On tool execution failure:
        Logs the error and leaves state.tool_result as None.
        Same reasoning: fail gracefully, stay observable, don't crash the graph.

    Args:
        state: Current AgentState. Reads tool_decision.

    Returns:
        Updated AgentState with tool_used and tool_result populated.
    """

    # Guard: tool_decision must have been set by llm_decision_node.
    # If it's None, the graph is wired incorrectly — log and return.
    if state.tool_decision is None:
        logger.error(
            "tool_executor_node called with no tool_decision in state. "
            "Check graph wiring — llm_decision_node must run first.",
            extra={"customer_id": state.customer_id},
        )
        return state

    # Explicit narrowing — the None guard above already confirms this,
    # but Pylance requires an assert to track it through attribute access.
    assert state.tool_decision is not None

    tool_name = state.tool_decision.tool_name

    # No-tool path: LLM determined no action is needed.
    # Leave tool_used and tool_result as None — response node handles this.
    if state.tool_decision.is_no_tool():
        logger.info(
            "tool_executor_node: no_tool decision — skipping execution.",
            extra={"customer_id": state.customer_id},
        )
        return state

    logger.info(
        "tool_executor_node started",
        extra={"customer_id": state.customer_id, "tool_name": tool_name},
    )

    # Registry lookup.
    tool_fn   = _TOOL_REGISTRY.get(tool_name)
    arg_builder = _ARGUMENT_BUILDERS.get(tool_name)

    if tool_fn is None or arg_builder is None:
        logger.error(
            "tool_executor_node: tool '%s' not found in registry.",
            tool_name,
            extra={"customer_id": state.customer_id},
        )
        # Do not raise — return state with tool_result = None.
        # Downstream response node will detect missing result and handle it.
        return state

    try:
        arguments = arg_builder(state)
        result    = tool_fn(**arguments)

        # Store the full raw result as the observation.
        # Do not flatten. Consumers extract what they need.
        state.tool_used   = tool_name
        state.tool_result = result

        logger.info(
            "tool_executor_node completed",
            extra={
                "tool_name":  tool_name,
                "tool_result": repr(result),
            },
        )

    except Exception as e:
        logger.error(
            "tool_executor_node: tool '%s' raised %s: %s",
            tool_name, type(e).__name__, e,
            extra={"customer_id": state.customer_id},
        )
        # tool_used and tool_result remain None.
        # Graph continues; response node handles missing result.

    return state