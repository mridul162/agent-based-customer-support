"""
app/nodes/agent_dispatch_node.py

Purpose:
--------
Read the routing decision from AgentState, look up the corresponding
specialist agent graph in AGENT_REGISTRY, invoke it, and merge the
agent's output back into the parent state.

Responsibilities:
-----------------
- Read state.routing_decision.agent_name.
- Look up the agent graph in AGENT_REGISTRY.
- Invoke the agent graph with current state.
- Merge the agent's returned state into the parent state.
- Return updated state.

This module DOES NOT:
---------------------
- Make routing decisions (router_node's responsibility).
- Know about tool selection, extraction, or validation.
- Generate customer responses directly.
- Know the internal structure of any specialist agent.

Architecture:
-------------
    router_node           → decides: "who handles this?"
          ↓
    agent_dispatch_node   → executes: "invoke the selected agent"  ← this file
          ↓
    END

Why a dedicated dispatch node instead of calling the agent from router_node?
-----------------------------------------------------------------------------
Separation of concerns: router_node decides, dispatch_node executes.
This mirrors the llm_decision_node / tool_executor_node split.
If the dispatch mechanism changes (e.g., async invocation, streaming),
only this node changes — routing logic is untouched.

How subgraph state merging works:
----------------------------------
LangGraph subgraphs return a state dict. The dispatch node updates
the parent AgentState with the returned values. Fields set by the
specialist agent (response, ticket_id, tool_used, tool_result, etc.)
are merged; fields not touched by the agent remain at their current values.
"""

import logging

from app.agents.agent_registry import AGENT_REGISTRY
from app.schemas.agent_state import AgentState

logger = logging.getLogger(__name__)

_FALLBACK_RESPONSE = (
    "We're unable to route your request right now. "
    "Your request has been noted and a support specialist will contact you shortly."
)


def agent_dispatch_node(state: AgentState) -> AgentState:
    """
    Invoke the specialist agent selected by router_node.

    Looks up AGENT_REGISTRY[routing_decision.agent_name], invokes the
    graph with the current state dict, and merges the result back.

    On missing routing_decision or unknown agent_name:
        Sets a fallback response and needs_human=True.
        Does not raise — keeps the graph running.

    Args:
        state: Current AgentState with routing_decision populated.

    Returns:
        Updated AgentState with specialist agent's outputs merged in.
    """

    if state.routing_decision is None:
        logger.error(
            "agent_dispatch_node: routing_decision is None. "
            "Check graph wiring — router_node must run first.",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        return state

    agent_name = state.routing_decision.agent_name
    agent_graph = AGENT_REGISTRY.get(agent_name)

    if agent_graph is None:
        logger.error(
            "agent_dispatch_node: agent '%s' not found in AGENT_REGISTRY.",
            agent_name,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        return state

    logger.info(
        "agent_dispatch_node: invoking '%s'.",
        agent_name,
        extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
    )

    try:
        # Invoke the specialist agent graph with the current state.
        # model_dump() converts AgentState to a plain dict for LangGraph.
        result = agent_graph.invoke(state.model_dump())

        # Merge the agent's output back into the parent state.
        # AgentState(**result) reconstructs the full typed state.
        merged = AgentState(**result)

        # Preserve routing_decision — the specialist agent doesn't know
        # about routing and won't set this field. Carry it forward.
        merged.routing_decision = state.routing_decision

        logger.info(
            "agent_dispatch_node: '%s' completed.",
            agent_name,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )

        return merged

    except Exception as e:
        logger.error(
            "agent_dispatch_node: agent '%s' raised %s: %s",
            agent_name, type(e).__name__, e,
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )
        state.needs_human = True
        state.response    = _FALLBACK_RESPONSE
        return state