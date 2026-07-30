"""
app/graphs/router_graph.py

Purpose:
--------
Top-level graph that routes customer messages to specialist agents.

The router graph owns request-level orchestration:
- initialize tracing
- load memory
- detect urgent escalation
- route to the selected specialist through AGENT_REGISTRY
- persist memory
- finalize tracing

Specialist agent branching is intentionally handled by agent_dispatch_node.
Adding faq_agent_graph or order_agent_graph only requires updating the
registry and router prompt, not adding one edge per agent here.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graphs.escalation_agent import escalation_agent_graph
from app.nodes.agent_dispatch_node import agent_dispatch_node
from app.nodes.escalation_detection_node import escalation_detection_node
from app.nodes.memory_loader_node import memory_loader_node
from app.nodes.memory_writer_node import memory_writer_node
from app.nodes.router_node import router_node
from app.nodes.subgraph_node import subgraph_node
from app.nodes.trace_finalizer_node import trace_finalizer_node
from app.nodes.trace_initializer_node import trace_initializer_node
from app.observability.tracing import traced
from app.schemas.agent_state import AgentState


def route_after_escalation_detection(state: AgentState) -> str:
    """
    Continue to specialist routing unless escalation was already detected.
    """

    if state.needs_human:
        return "escalation_agent"

    return "router_node"


def build_router_graph() -> CompiledStateGraph:
    """
    Construct and compile the top-level routing graph.

    Flow:
        START
          -> trace_initializer_node
          -> memory_loader_node
          -> escalation_detection_node
          -> router_node or escalation_agent
          -> agent_dispatch_node when routed
          -> memory_writer_node
          -> trace_finalizer_node
          -> END
    """

    graph = StateGraph(AgentState)

    graph.add_node(
        "trace_initializer_node",
        traced("trace_initializer_node")(trace_initializer_node),
    )
    graph.add_node(
        "memory_loader_node",
        traced("memory_loader_node")(memory_loader_node),
    )
    graph.add_node(
        "escalation_detection_node",
        traced("escalation_detection_node")(escalation_detection_node),
    )
    graph.add_node(
        "router_node",
        traced("router_node")(router_node),
    )
    graph.add_node(
        "agent_dispatch_node",
        traced("agent_dispatch_node")(agent_dispatch_node),
    )
    graph.add_node(
        "escalation_agent",
        traced("escalation_agent")(
            subgraph_node(escalation_agent_graph)
        ),
    )
    graph.add_node(
        "memory_writer_node",
        traced("memory_writer_node")(memory_writer_node),
    )
    graph.add_node(
        "trace_finalizer_node",
        traced("trace_finalizer_node")(trace_finalizer_node),
    )

    graph.add_edge(START, "trace_initializer_node")
    graph.add_edge("trace_initializer_node", "memory_loader_node")
    graph.add_edge("memory_loader_node", "escalation_detection_node")

    graph.add_conditional_edges(
        "escalation_detection_node",
        route_after_escalation_detection,
        {
            "escalation_agent": "escalation_agent",
            "router_node": "router_node",
        },
    )

    graph.add_edge("router_node", "agent_dispatch_node")
    graph.add_edge("agent_dispatch_node", "memory_writer_node")
    graph.add_edge("escalation_agent", "memory_writer_node")
    graph.add_edge("memory_writer_node", "trace_finalizer_node")
    graph.add_edge("trace_finalizer_node", END)

    return graph.compile()


router_graph = build_router_graph()
