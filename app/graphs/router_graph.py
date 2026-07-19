"""
app/graphs/router_graph.py

Purpose:
--------
Top-level graph that routes customer messages to specialist agents.

This is the entry point for the multi-agent platform. It replaces
react_graph as the primary graph invoked by the API layer.

Architecture:
-------------
    START
      ↓
    router_node           → LLM selects which agent handles this
      ↓                     writes: state.routing_decision
    agent_dispatch_node   → invokes the selected specialist agent
      ↓                     merges: agent's state output into parent state
    END

Why no conditional edges at the router level?
---------------------------------------------
agent_dispatch_node handles the branching internally via AGENT_REGISTRY.
A conditional edge here would require the graph to know agent names,
duplicating registry knowledge into the graph wiring.

The dispatch node pattern keeps the graph linear and registry-driven:
    router → dispatch → (registry lookup inside dispatch) → END

This mirrors the same decision made in react_graph: the no_tool and
needs_clarification branches are handled inside nodes, not as graph edges.

Relationship to react_graph:
-----------------------------
react_graph remains unchanged — it is now the ticket_agent implementation,
registered in AGENT_REGISTRY["ticket_agent"].
router_graph is a new top-level graph that delegates to react_graph
(and future specialist agents) via agent_dispatch_node.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.nodes.agent_dispatch_node import agent_dispatch_node
from app.nodes.router_node import router_node
from app.schemas.agent_state import AgentState


def build_router_graph() -> CompiledStateGraph:
    """
    Construct and compile the top-level routing graph.

    Graph structure:
        START → router_node → agent_dispatch_node → END

    Returns:
        CompiledStateGraph ready to invoke with:
            router_graph.invoke({"customer_id": ..., "message": ...})
    """

    graph = StateGraph(AgentState)

    graph.add_node("router_node",         router_node)
    graph.add_node("agent_dispatch_node", agent_dispatch_node)

    graph.add_edge(START,                "router_node")
    graph.add_edge("router_node",        "agent_dispatch_node")
    graph.add_edge("agent_dispatch_node", END)

    return graph.compile()


router_graph = build_router_graph()