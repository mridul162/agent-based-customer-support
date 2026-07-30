"""
tests/validate_faq_agent_graph.py

Purpose:
--------
Validate the FAQ specialist agent graph.

This script verifies:
- faq_agent_graph invokes retrieve_knowledge_tool.
- The grounded answer is written to AgentState.response.
- Tool execution metrics are recorded.
- The FAQ graph is registered in AGENT_REGISTRY.
- agent_dispatch_node can invoke the FAQ graph from a RoutingDecision.

run:
    python -m tests.validate_faq_agent_graph
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.agent_registry import AGENT_REGISTRY
from app.graphs.faq_agent import faq_agent_graph
from app.nodes.agent_dispatch_node import agent_dispatch_node
from app.schemas.agent_state import AgentState
from app.schemas.execution_trace import ExecutionTrace
from app.schemas.routing_decision import RoutingDecision


PASS = "PASS"
FAIL = "FAIL"


def check(condition: bool, message: str) -> None:
    status = PASS if condition else FAIL
    symbol = "[OK]" if condition else "[FAIL]"
    print(f"  {symbol} {status:<6} {message}")

    if not condition:
        raise AssertionError(message)


def build_state() -> AgentState:
    return AgentState(
        request_id=str(uuid4()),
        customer_id="customer-faq-validation",
        message="What is your refund policy?",
        execution_trace=ExecutionTrace(
            request_id=str(uuid4()),
            customer_id="customer-faq-validation",
            started_at=datetime.now(UTC),
        ),
    )


def fake_retrieve_knowledge_tool(
    question: str,
    execution_trace=None,
) -> str:
    return (
        "Refund requests are reviewed after the returned item is received. "
        "Approved refunds are returned to the original payment method."
    )


def validate_direct_graph_invocation() -> None:
    print("[1] Direct FAQ graph invocation")

    state = build_state()

    with patch(
        "app.graphs.faq_agent.retrieve_knowledge_tool",
        side_effect=fake_retrieve_knowledge_tool,
    ) as tool:
        result = faq_agent_graph.invoke(state.model_dump())

    result_state = AgentState(**result)
    trace = result_state.execution_trace

    check(tool.called, "retrieve_knowledge_tool was invoked")
    check(result_state.response is not None, "Response populated")
    assert result_state.response is not None
    check("refund" in result_state.response.lower(), "Response is grounded")
    check(
        result_state.tool_used == "retrieve_knowledge_tool",
        "tool_used recorded",
    )
    check(
        result_state.tool_result == result_state.response,
        "tool_result preserves grounded answer",
    )
    check(trace is not None, "ExecutionTrace preserved")

    if trace is None:
        return

    check(
        any(node.node_name == "faq_answer_node" for node in trace.nodes),
        "FAQ node trace recorded",
    )
    check(len(trace.tool_metrics) == 1, "Tool metrics recorded")
    check(trace.tool_metrics[0].success, "Tool metric marked successful")
    check(
        trace.metrics.tool_used == "retrieve_knowledge_tool",
        "Summary metric records retrieval tool",
    )


def validate_registry_dispatch() -> None:
    print("[2] Registry dispatch")

    check("faq_agent" in AGENT_REGISTRY, "faq_agent registered")

    state = build_state()
    state.routing_decision = RoutingDecision(
        agent_name="faq_agent",
        reasoning="Customer asked a knowledge-base question.",
    )

    with patch(
        "app.graphs.faq_agent.retrieve_knowledge_tool",
        side_effect=fake_retrieve_knowledge_tool,
    ):
        result_state = agent_dispatch_node(state)

    check(result_state.response is not None, "Dispatch returns FAQ response")
    assert result_state.response is not None
    check("refund" in result_state.response.lower(), "Dispatch response grounded")
    check(
        result_state.routing_decision is not None
        and result_state.routing_decision.agent_name == "faq_agent",
        "Routing decision preserved",
    )


def main() -> None:
    print("=" * 64)
    print("  FAQ Agent Graph Validation")
    print("=" * 64)
    print()

    validate_direct_graph_invocation()
    print()

    validate_registry_dispatch()
    print()

    print("=" * 64)
    print("  FAQ Agent Graph Validation Completed")
    print("=" * 64)


if __name__ == "__main__":
    main()
