"""
app/graphs/react_graph.py

Purpose:
--------
Ticket-agent graph built from the shared ReAct-style tool workflow.

Now that faq_agent_graph and order_agent_graph exist, this graph should be
treated as the ticket specialist registered as AGENT_REGISTRY["ticket_agent"].
It remains useful for support tickets and ticket lookup, while FAQ and order
requests are routed to their own specialist graphs by router_graph.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.nodes.argument_extraction_node import argument_extraction_node
from app.nodes.argument_validation_node import argument_validation_node
from app.nodes.response_node import response_node
from app.nodes.ticket_tool_decision_node import ticket_tool_decision_node
from app.nodes.tool_executor_node import tool_executor_node
from app.observability.tracing import traced
from app.schemas.agent_state import AgentState


def build_react_graph() -> CompiledStateGraph:
    """
    Construct and compile the ticket-agent ReAct workflow.

    Flow:
        START
          -> ticket_tool_decision_node
          -> argument_extraction_node
          -> argument_validation_node
          -> tool_executor_node
          -> response_node
          -> END
    """

    graph = StateGraph(AgentState)

    graph.add_node(
        "ticket_tool_decision_node",
        traced("ticket_tool_decision_node")(ticket_tool_decision_node),
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

    graph.add_edge(START, "ticket_tool_decision_node")
    graph.add_edge("ticket_tool_decision_node", "argument_extraction_node")
    graph.add_edge("argument_extraction_node", "argument_validation_node")
    graph.add_edge("argument_validation_node", "tool_executor_node")
    graph.add_edge("tool_executor_node", "response_node")
    graph.add_edge("response_node", END)

    return graph.compile()


react_graph = build_react_graph()
ticket_agent_graph = react_graph
