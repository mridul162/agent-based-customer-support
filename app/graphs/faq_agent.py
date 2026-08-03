"""
app/graphs/faq_agent.py

Purpose:
--------
Specialist FAQ agent for grounded knowledge-base answers.

Architecture:
-------------
    faq_agent_graph
          |
          v
    faq_answer_node
          |
          v
    retrieve_knowledge_tool
          |
          v
    RetrievalService -> AnswerGenerator -> LLMService
"""

import logging
from datetime import UTC, datetime

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.observability.tracing import traced
from app.schemas.agent_state import AgentState
from app.schemas.tool_metrics import ToolMetrics
from app.tools.retrieve_knowledge_tool import retrieve_knowledge_tool

logger = logging.getLogger(__name__)

_TOOL_NAME = "retrieve_knowledge_tool"


def faq_answer_node(state: AgentState) -> AgentState:
    """
    Answer a customer FAQ/policy/product question from the knowledge base.

    Reads:  state.message, state.execution_trace
    Writes: state.tool_used, state.tool_result, state.response
    """

    logger.info(
        "faq_answer_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
        },
    )

    started = datetime.now(UTC)

    try:
        answer = retrieve_knowledge_tool(
            question=state.message,
            execution_trace=state.execution_trace,
        )

        finished = datetime.now(UTC)

        state.tool_used = _TOOL_NAME
        state.tool_result = answer
        state.response = answer

        trace = state.execution_trace

        if trace is not None:
            trace.tool_metrics.append(
                ToolMetrics(
                    tool_name=_TOOL_NAME,
                    started_at=started,
                    finished_at=finished,
                    duration_ms=(finished - started).total_seconds() * 1000,
                    success=True,
                )
            )
            trace.metrics.tool_used = _TOOL_NAME

        logger.info(
            "faq_answer_node completed",
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )

    except Exception as exc:
        finished = datetime.now(UTC)

        trace = state.execution_trace

        if trace is not None:
            trace.tool_metrics.append(
                ToolMetrics(
                    tool_name=_TOOL_NAME,
                    started_at=started,
                    finished_at=finished,
                    duration_ms=(finished - started).total_seconds() * 1000,
                    success=False,
                    error=str(exc),
                )
            )

        logger.error(
            "faq_answer_node failed: %s",
            repr(exc),
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )

        state.needs_human = True
        state.response = (
            "I could not answer that from the knowledge base right now. "
            "I can create a support ticket so a specialist can help."
        )

    return state


def build_faq_agent_graph() -> CompiledStateGraph:
    """
    Build the FAQ specialist agent graph.
    """

    graph = StateGraph(AgentState)
    graph.add_node("faq_answer_node", traced("faq_answer_node")(faq_answer_node))
    graph.add_edge(START, "faq_answer_node")
    graph.add_edge("faq_answer_node", END)
    return graph.compile()


faq_agent_graph = build_faq_agent_graph()
