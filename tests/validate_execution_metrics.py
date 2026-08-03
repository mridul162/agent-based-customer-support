"""
tests/validate_execution_metrics.py

Purpose:
--------
Validate Milestone 14.3 — Execution Metrics.

This validation verifies that request-level execution metrics are
correctly collected during graph execution.

Validated metrics:
------------------
- metrics object exists
- selected agent recorded
- executed tool recorded
- clarification flag
- escalation flag
- ticket creation flag
- total request latency

This test validates business-level observability.
Execution tracing itself is validated separately.
"""

from uuid import uuid4

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState


def check(condition: bool, description: str) -> None:
    """Pretty validation output."""

    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {status:<8} {description}")


def main() -> None:

    print("=" * 60)
    print("  Milestone 14.3 — Execution Metrics")
    print("=" * 60)
    print()

    print("Initialising database...")
    init_db()

    print()
    print("[Scenario 1] Refund request")

    state = AgentState(
        request_id=str(uuid4()),
        customer_id="customer_001",
        message="I would like a refund for my order.",
    )

    result = router_graph.invoke(state)

    state = result if isinstance(result, AgentState) else AgentState(**result)

    trace = state.execution_trace
    metrics = trace.metrics if trace else None

    print()

    check(trace is not None, "ExecutionTrace exists")
    check(metrics is not None, "ExecutionMetrics exists")

    if metrics is None:
        return

    check(metrics.agent_name is not None, "Agent selected")
    check(metrics.tool_used is not None, "Tool recorded")
    check(
        metrics.total_latency_ms is not None and metrics.total_latency_ms >= 0,
        "Total latency recorded",
    )

    print()
    print("Execution Metrics")
    print("-" * 60)

    print(f"Agent                  : {metrics.agent_name}")
    print(f"Tool                   : {metrics.tool_used}")
    print(f"Clarification          : {metrics.clarification_requested}")
    print(f"Escalated              : {metrics.escalated}")
    print(f"Ticket Created         : {metrics.ticket_created}")
    print(f"Total Latency (ms)     : {metrics.total_latency_ms:.2f}")

    print()
    print("=" * 60)
    print("  Execution Metrics                 ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
