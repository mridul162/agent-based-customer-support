from collections.abc import Callable
from langgraph.graph.state import CompiledStateGraph
from app.schemas.agent_state import AgentState


def subgraph_node(
    graph: CompiledStateGraph,
) -> Callable[[AgentState], AgentState]:
    """
    Wrap a compiled LangGraph subgraph so it can be registered as a
    normal graph node.
    """

    def wrapper(state: AgentState) -> AgentState:
        result = graph.invoke(state.model_dump())
        return AgentState(**result)

    return wrapper