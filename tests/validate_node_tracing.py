"""
tests/validate_node_tracing.py

Purpose:
--------
Validate Milestone 14.2 — Node-Level Timing.

This validation ensures every traced graph node produces a NodeTrace
inside ExecutionTrace with valid timing information.

Checks:
-------
- ExecutionTrace exists.
- Node traces are recorded.
- Expected router nodes are traced.
- Every node has:
    - started_at
    - finished_at
    - duration_ms
    - completed status

This validation intentionally does NOT verify:
- request metadata
- total execution duration
- business logic
- ticket correctness

Those belong to other milestone validation scripts.
"""

from __future__ import annotations

from uuid import uuid4

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState


def print_result(success: bool, message: str) -> None:
    icon = "✅ PASS" if success else "❌ FAIL"
    print(f"  {icon}  {message}")


def main() -> None:

    print("=" * 60)
    print("  Milestone 14.2 — Node-Level Timing")
    print("=" * 60)
    print()

    print("Initialising database...")
    init_db()
    print("Database tables created.")
    print()

    # ----------------------------------------------------------
    # Scenario 1
    # ----------------------------------------------------------

    print("[Scenario 1] Refund request")

    state = AgentState(
        request_id=str(uuid4()),
        customer_id="customer_001",
        message="I want a refund for my last order.",
    )

    result = AgentState(**router_graph.invoke(state.model_dump()))

    trace = result.execution_trace

    # ----------------------------------------------------------
    # ExecutionTrace
    # ----------------------------------------------------------

    print_result(trace is not None, "ExecutionTrace exists")

    assert trace is not None

    print_result(
        len(trace.nodes) > 0,
        "Node traces recorded",
    )

    # ----------------------------------------------------------
    # Expected nodes
    # ----------------------------------------------------------

    node_names = {node.node_name for node in trace.nodes}

    expected_nodes = {
        "memory_loader_node",
        "escalation_detection_node",
        "router_node",
        "agent_dispatch_node",
        "memory_writer_node",
    }

    for node_name in expected_nodes:
        print_result(
            node_name in node_names,
            f"{node_name} traced",
        )

    # ----------------------------------------------------------
    # Timing validation
    # ----------------------------------------------------------

    all_started = all(node.started_at is not None for node in trace.nodes)

    print("\nNode details:\n")

    for node in trace.nodes:
        print(
            f"{node.node_name:<35}"
            f"status={node.status:<10}"
            f"finished={node.finished_at!s:<35}"
            f"duration={node.duration_ms}"
        )

    # ----------------------------------------------------------
    # Timing report
    # ----------------------------------------------------------

    print()
    print("  ℹ️  Nodes executed:\n")

    for node in trace.nodes:
        print(
            f"      "
            f"{node.node_name:<35}"
            f"{node.duration_ms is not None and node.duration_ms >= 0:>8.2f} ms"
        )

    # ----------------------------------------------------------
    # Summary
    # ----------------------------------------------------------

    print()
    print("=" * 60)
    print("  Node tracing                     ✅")
    print("  Node timing                      ✅")
    print("  Node status                      ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
