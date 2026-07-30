"""
app/graphs/order_agent.py

Purpose:
--------
Specialist order-management agent.

The order agent uses its own LLM decision node and prompt to select only
order tools, then reuses the shared extraction, validation, execution, and
response nodes.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.nodes.argument_extraction_node import argument_extraction_node
from app.nodes.argument_validation_node import argument_validation_node
from app.nodes.order_tool_decision_node import order_tool_decision_node
from app.nodes.response_node import response_node
from app.nodes.tool_executor_node import tool_executor_node
from app.observability.tracing import traced
from app.schemas.agent_state import AgentState


def build_order_agent_graph() -> CompiledStateGraph:
    """
    Build the order specialist agent graph.
    """

    graph = StateGraph(AgentState)

    graph.add_node(
        "order_tool_decision_node",
        traced("order_tool_decision_node")(order_tool_decision_node),
    )
    graph.add_node(
        "argument_extraction_node",
        traced("argument_extraction_node")(argument_extraction_node),
    )
    graph.add_node(
        "argument_validation_node",
        traced("argument_validation_node")(argument_validation_node),
    )
    graph.add_node(
        "tool_executor_node",
        traced("tool_executor_node")(tool_executor_node),
    )
    graph.add_node(
        "response_node",
        traced("response_node")(response_node),
    )

    graph.add_edge(START, "order_tool_decision_node")
    graph.add_edge("order_tool_decision_node", "argument_extraction_node")
    graph.add_edge("argument_extraction_node", "argument_validation_node")
    graph.add_edge("argument_validation_node", "tool_executor_node")
    graph.add_edge("tool_executor_node", "response_node")
    graph.add_edge("response_node", END)

    return graph.compile()


order_agent_graph = build_order_agent_graph()
