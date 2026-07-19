"""
app/agents/agent_registry.py

Purpose:
--------
Single source of truth for all specialist agent graphs.

Maps agent_name strings (matching RoutingDecision.agent_name) to
compiled LangGraph subgraphs. The agent_dispatch_node looks up
the correct graph here and invokes it.

Adding a new agent:
    1. Build the agent's compiled graph.
    2. Add one entry to AGENT_REGISTRY.
    3. Update the router prompt.
    No other files change.

Why a dict of compiled graphs, not a dict of functions?
--------------------------------------------------------
Each agent is a full LangGraph workflow with its own nodes and edges.
Storing the compiled graph (CompiledStateGraph) means the dispatch node
calls graph.invoke(state.model_dump()) with no knowledge of the agent's
internal structure — clean separation between routing and execution.
"""

from langgraph.graph.state import CompiledStateGraph

from app.graphs.react_graph import react_graph
from app.schemas.agent_state import AgentState


# ---------------------------------------------------------------------------
# Stub graphs for agents not yet implemented.
# Each stub sets state.response directly and returns — no tools, no LLM.
# Stubs allow the router architecture to be validated end-to-end before
# every specialist agent is fully built.
# ---------------------------------------------------------------------------

def _build_faq_stub() -> CompiledStateGraph:
    """
    Minimal FAQ agent stub — returns a fixed not-implemented response.
    Replaced with a real FAQ graph in a future milestone.
    """
    from langgraph.graph import END, START, StateGraph

    def faq_stub_node(state: AgentState) -> AgentState:
        state.response = (
            "Our FAQ agent is not yet available. "
            "For general questions, please visit our help center or "
            "let me create a support ticket for you."
        )
        return state

    graph = StateGraph(AgentState)
    graph.add_node("faq_stub", faq_stub_node)
    graph.add_edge(START, "faq_stub")
    graph.add_edge("faq_stub", END)
    return graph.compile()


def _build_order_stub() -> CompiledStateGraph:
    """
    Minimal order agent stub — returns a fixed not-implemented response.
    Replaced with a real order graph in a future milestone.
    """
    from langgraph.graph import END, START, StateGraph

    def order_stub_node(state: AgentState) -> AgentState:
        state.response = (
            "Our order management agent is not yet available. "
            "I'll create a support ticket so our team can assist "
            "with your order inquiry."
        )
        return state

    graph = StateGraph(AgentState)
    graph.add_node("order_stub", order_stub_node)
    graph.add_edge(START, "order_stub")
    graph.add_edge("order_stub", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# Agent Registry
#
# Keys must match AgentType enum values and RoutingDecision.agent_name
# strings exactly.
# ---------------------------------------------------------------------------

AGENT_REGISTRY: dict[str, CompiledStateGraph] = {
    "ticket_agent": react_graph,          # Full implementation — Milestones 4–8
    "faq_agent":    _build_faq_stub(),    # Stub — future milestone
    "order_agent":  _build_order_stub(),  # Stub — future milestone
}