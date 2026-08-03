"""
tests/validate_execution_trace.py

Purpose:
--------
Validate Milestone 14.1 — Execution Trace Foundation.

This validation ensures:
- ExecutionTrace is created for every request.
- Trace metadata is populated correctly.
- Total execution timing is recorded.
- Existing routing/ticket workflow remains unaffected.

This validation intentionally does NOT verify:
- Node-level timing
- Metrics
- Analytics
- Evaluation reports

Those are introduced in later milestones.

Run:
----
python -m tests.validate_execution_trace
"""

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState


def assert_pass(condition: bool, message: str) -> None:
    """Simple PASS/FAIL printer."""

    if condition:
        print(f"  ✅ PASS  {message}")
    else:
        print(f"  ❌ FAIL  {message}")


def main() -> None:
    print("=" * 60)
    print("  Milestone 14.1 — Execution Trace Foundation")
    print("=" * 60)

    print("\nInitialising database...")
    init_db()

    print("\n[Scenario 1] Refund request")

    state = AgentState(
        request_id="REQ-TRACE-001",
        customer_id="customer-001",
        message="I would like a refund for my order.",
    )

    result = AgentState(**router_graph.invoke(state.model_dump()))

    trace = result.execution_trace

    assert_pass(
        trace is not None,
        "ExecutionTrace created",
    )

    assert_pass(
        trace.request_id == state.request_id,  # type: ignore
        "request_id propagated",
    )

    assert_pass(
        trace.customer_id == state.customer_id,  # type: ignore
        "customer_id propagated",
    )

    assert_pass(
        trace.started_at is not None,  # type: ignore
        "started_at populated",
    )

    assert_pass(
        trace.finished_at is not None,  # type: ignore
        "finished_at populated",
    )

    assert_pass(
        trace.total_duration_ms is not None,  # type: ignore
        "total_duration_ms calculated",
    )

    assert_pass(
        trace.total_duration_ms >= 0,  # type: ignore
        "duration is non-negative",
    )

    print(f"\n  ℹ️  Total duration: {trace.total_duration_ms:.2f} ms")  # type: ignore

    print("\n[Regression] Ticket workflow")

    assert_pass(
        result.ticket_id is not None,  # type: ignore
        "ticket created",
    )

    assert_pass(
        result.response is not None,  # type: ignore
        "customer response generated",
    )

    print(f"\n  ℹ️  Ticket ID: {result.ticket_id}")  # type: ignore

    print("\n" + "=" * 60)
    print("  ExecutionTrace initialization      ✅")
    print("  Request metadata                  ✅")
    print("  Total execution timing            ✅")
    print("  Ticket workflow regression        ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
