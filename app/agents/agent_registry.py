"""
app/agents/agent_registry.py

Purpose:
--------
Single source of truth for all specialist agent graphs.

Maps agent_name strings to compiled LangGraph subgraphs. The
agent_dispatch_node looks up the correct graph here and invokes it.
"""

from langgraph.graph.state import CompiledStateGraph

from app.graphs.escalation_agent import escalation_agent_graph
from app.graphs.faq_agent import faq_agent_graph
from app.graphs.order_agent import order_agent_graph
from app.graphs.react_graph import react_graph

AGENT_REGISTRY: dict[str, CompiledStateGraph] = {
    "ticket_agent": react_graph,
    "faq_agent": faq_agent_graph,
    "order_agent": order_agent_graph,
    "escalation_agent": escalation_agent_graph,
}
