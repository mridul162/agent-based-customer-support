"""
app/graphs/escalation_agent.py

Purpose:
--------
Specialist agent that handles human escalation requests.

Responsibilities:
-----------------
- Read escalation_reason and escalation_queue from state.
- Create an escalation record in the database.
- Generate a customer-facing response with the escalation ID.
- Set state.escalation_response and state.response.

This agent is simple by design:
    It has no tool selection, no extraction, no validation.
    It always creates an escalation — that decision was made upstream
    by escalation_detection_node or the router.

Architecture:
-------------
    escalation_agent_graph
          ↓
    escalate_node    ← single node: create escalation + build response
          ↓
    END
"""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.schemas.agent_state import AgentState
from app.schemas.escalation import CreateEscalationRequest, EscalationQueue
from app.tools.escalation_tools import create_escalation_tool

logger = logging.getLogger(__name__)

_ESCALATION_RESPONSE_TEMPLATE = (
    "I understand this requires immediate attention from our support team.\n\n"
    "Your request has been escalated to a specialist.\n\n"
    "Escalation ID: {escalation_id}\n\n"
    "A member of our {queue} team will contact you as soon as possible."
)


def escalate_node(state: AgentState) -> AgentState:
    """
    Create a human escalation record and generate the customer response.

    Reads:  state.customer_id, state.escalation_reason, state.escalation_queue
    Writes: state.escalation_response, state.response
    """
    reason = state.escalation_reason or "Human assistance requested."
    queue  = state.escalation_queue  or EscalationQueue.GENERAL.value

    try:
        escalation = create_escalation_tool(
            customer_id=state.customer_id,
            reason=reason,
            queue=queue,
        )

        state.escalation_response = escalation
        state.response = _ESCALATION_RESPONSE_TEMPLATE.format(
            escalation_id=escalation.escalation_id,
            queue=queue.replace("_", " ").title(),
        )

        logger.info(
            "escalate_node: escalation created.",
            extra={
                "request_id":    state.request_id,
                "customer_id":   state.customer_id,
                "escalation_id": escalation.escalation_id,
                "queue":         queue,
            },
        )

    except Exception as e:
        logger.error(
            "escalate_node: failed to create escalation: %s", repr(e),
            extra={
                "request_id":  state.request_id,
                "customer_id": state.customer_id,
            },
        )
        state.response = (
            "Your request requires human assistance. "
            "Please contact our support team directly. "
            "We apologize for any inconvenience."
        )

    return state


def build_escalation_agent() -> CompiledStateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("escalate_node", escalate_node)
    graph.add_edge(START, "escalate_node")
    graph.add_edge("escalate_node", END)
    return graph.compile()


escalation_agent_graph = build_escalation_agent()