"""
app/graphs/react_graph.py

Purpose:
--------
Wire llm_decision_node, tool_executor_node, and response_node into a
complete LangGraph ReAct workflow and compile it into a runnable graph.

Responsibilities:
-----------------
- Register all three ReAct nodes with the StateGraph.
- Define the linear edge sequence: START → decision → executor → response → END.
- Compile and expose the graph as a module-level instance.

This module DOES NOT:
---------------------
- Implement node logic (each node owns its own file).
- Own prompts, tools, or business rules.
- Manage memory, retrieval, or multi-agent routing (future milestones).
- Handle conditional routing (no conditional edges in this graph yet).

Architecture — ReAct loop wired as a graph:
--------------------------------------------
    START
      ↓
    llm_decision_node     → Reason:   LLM decides tool_name + reasoning
      ↓                               writes: state.tool_decision
    tool_executor_node    → Act:      executes the selected tool
      ↓                               writes: state.tool_used, state.tool_result
    response_node         → Observe   reads tool_result (observation)
      ↓                     + Respond: writes state.response, state.needs_human
    END

Why linear edges (no conditional edges yet)?
    The LLM decision node already handles the no_tool case internally —
    tool_executor_node skips execution when is_no_tool() is True, and
    response_node handles the None tool_result gracefully.
    Conditional edges will be introduced when routing to different
    specialist agents or escalation workflows is needed.

State evolution across nodes:
------------------------------
Each node adds to state without removing prior contributions:

    After llm_decision_node:
        state.tool_decision  ← populated

    After tool_executor_node:
        state.tool_decision  ← preserved
        state.tool_used      ← populated (or None if no_tool)
        state.tool_result    ← populated (or None if no_tool/failure)

    After response_node:
        state.tool_decision  ← preserved
        state.tool_used      ← preserved
        state.tool_result    ← preserved (never mutated)
        state.response       ← populated
        state.needs_human    ← set if escalation required

The final state is a complete, non-destructive record of the execution.
This property makes multi-agent state sharing possible in future milestones.

Relationship to support_graph.py:
----------------------------------
support_graph.py uses rule-based intent detection and deterministic routing.
react_graph.py uses LLM-based decision making.
Both coexist — they represent different orchestration strategies.
react_graph.py is the foundation for future multi-agent work.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.nodes.llm_decision_node import llm_decision_node
from app.nodes.response_node import response_node
from app.nodes.tool_executor_node import tool_executor_node
from app.schemas.agent_state import AgentState


def build_react_graph() -> CompiledStateGraph:
    """
    Construct and compile the ReAct workflow graph.

    Node registration order matches execution order for readability —
    not a technical requirement, but a convention worth keeping.

    Returns:
        CompiledStateGraph ready to invoke with:
            react_graph.invoke({"customer_id": ..., "message": ...})
    """

    graph = StateGraph(AgentState)

    # ------------------------------------------------------------------
    # Register Nodes
    # String names are used in add_edge() calls below.
    # ------------------------------------------------------------------

    graph.add_node("llm_decision_node",   llm_decision_node)
    graph.add_node("tool_executor_node",  tool_executor_node)
    graph.add_node("response_node",       response_node)

    # ------------------------------------------------------------------
    # Define Edges — linear sequence, no conditional routing yet.
    # ------------------------------------------------------------------

    graph.add_edge(START,                "llm_decision_node")
    graph.add_edge("llm_decision_node",  "tool_executor_node")
    graph.add_edge("tool_executor_node", "response_node")
    graph.add_edge("response_node",      END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Module-level compiled graph instance.
# Imported and invoked by the API layer, validation scripts, or tests.
# ---------------------------------------------------------------------------

react_graph = build_react_graph()