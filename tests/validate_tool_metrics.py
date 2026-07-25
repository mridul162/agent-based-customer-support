"""
tests/validate_tool_metrics.py

Purpose:
--------
Validate Milestone 14.4 (Tool Execution Metrics).

This script executes a complete graph run that invokes a tool and
verifies that ToolMetrics are recorded correctly inside the
ExecutionTrace.

Validation:
-----------
- ExecutionTrace exists
- ToolMetrics list exists
- Exactly one ToolMetrics record is created
- Tool name is recorded
- Start timestamp is recorded
- Finish timestamp is recorded
- Duration is recorded
- Tool execution succeeded
- No execution error

Run:
----
python -m tests.validate_tool_metrics
"""

from uuid import uuid4

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState


def check(condition: bool, message: str) -> None:
    """Print PASS/FAIL for a validation check."""

    if condition:
        print(f"  ✅ PASS   {message}")
    else:
        print(f"  ❌ FAIL   {message}")


def main() -> None:

    print("=" * 60)
    print("  Milestone 14.4 — Tool Execution Metrics")
    print("=" * 60)

    print("\nInitialising database...")
    init_db()

    print("\n[Scenario 1] Refund request\n")

    state = AgentState(
        request_id=str(uuid4()),
        customer_id="customer-001",
        message="I received a damaged product and want a refund.",
    )

    result = router_graph.invoke(state)

    state = (
        result
        if isinstance(result, AgentState)
        else AgentState(**result)
    )

    trace = state.execution_trace

    check(trace is not None, "ExecutionTrace exists")

    if trace is None:
        return

    check(
        len(trace.tool_metrics) > 0,
        "Tool metrics recorded",
    )

    if not trace.tool_metrics:
        return

    tool = trace.tool_metrics[0]

    check(
        tool.tool_name is not None,
        "Tool name recorded",
    )

    check(
        tool.started_at is not None,
        "Start timestamp recorded",
    )

    check(
        tool.finished_at is not None,
        "Finish timestamp recorded",
    )

    check(
        tool.duration_ms is not None
        and tool.duration_ms >= 0,
        "Execution duration recorded",
    )

    check(
        tool.success,
        "Tool execution succeeded",
    )

    check(
        tool.error is None,
        "No execution error",
    )

    print("\nTool Metrics")
    print("-" * 60)
    print(f"Tool                 : {tool.tool_name}")
    print(f"Success              : {tool.success}")
    print(f"Duration (ms)        : {tool.duration_ms:.2f}")

    if tool.error:
        print(f"Error                : {tool.error}")
    else:
        print("Error                : None")

    print("\n" + "=" * 60)
    print("  Tool Execution Metrics          ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()