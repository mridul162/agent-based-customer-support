"""
app/graphs/order_agent.py

Purpose:
--------
Specialist order-management agent.

Architecture:
-------------
    START
      |
      v
    order_decision_node
      |
      v
    argument_extraction_node
      |
      v
    argument_validation_node
      |
      v
    tool_executor_node
      |
      v
    response_node
      |
      v
    END
"""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.nodes.argument_extraction_node import argument_extraction_node
from app.nodes.argument_validation_node import argument_validation_node
from app.nodes.response_node import response_node
from app.nodes.tool_executor_node import tool_executor_node
from app.observability.tracing import traced
from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import ToolDecision

logger = logging.getLogger(__name__)


def order_decision_node(state: AgentState) -> AgentState:
    """
    Select the order tool for the customer's order-management request.

    This specialist node is deterministic because order operations map cleanly
    to command keywords and all required entities are extracted separately.
    """

    message = state.message.lower()

    if any(word in message for word in ("cancel", "cancellation")):
        tool_name = "cancel_order_tool"
        reasoning = "Customer wants to cancel an order."

    elif (
        "address" in message
        and any(word in message for word in ("update", "change", "deliver", "ship"))
    ):
        tool_name = "update_delivery_address_tool"
        reasoning = "Customer wants to update an order delivery address."

    elif any(
        phrase in message
        for phrase in (
            "delivery time",
            "estimated delivery",
            "eta",
            "when will",
            "when does",
            "arrive",
            "delivered",
        )
    ):
        tool_name = "estimate_delivery_time_tool"
        reasoning = "Customer wants a delivery estimate for an order."

    else:
        tool_name = "get_order_status_tool"
        reasoning = "Customer wants order status or tracking information."

    state.tool_decision = ToolDecision(
        tool_name=tool_name,
        reasoning=reasoning,
    )

    logger.info(
        "order_decision_node completed",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_name,
        },
    )

    return state


def build_order_agent_graph() -> CompiledStateGraph:
    """
    Build the order specialist agent graph.
    """

    graph = StateGraph(AgentState)

    graph.add_node("order_decision_node", traced("order_decision_node")(order_decision_node))
    graph.add_node("argument_extraction_node", traced("argument_extraction_node")(argument_extraction_node))
    graph.add_node("argument_validation_node", traced("argument_validation_node")(argument_validation_node))
    graph.add_node("tool_executor_node", traced("tool_executor_node")(tool_executor_node))
    graph.add_node("response_node", traced("response_node")(response_node))

    graph.add_edge(START, "order_decision_node")
    graph.add_edge("order_decision_node", "argument_extraction_node")
    graph.add_edge("argument_extraction_node", "argument_validation_node")
    graph.add_edge("argument_validation_node", "tool_executor_node")
    graph.add_edge("tool_executor_node", "response_node")
    graph.add_edge("response_node", END)

    return graph.compile()


order_agent_graph = build_order_agent_graph()
