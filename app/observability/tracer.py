"""
app/observability/tracer.py

Purpose:
--------
Provides utilities for recording execution traces during LangGraph
execution.

The ExecutionTracer operates directly on an ExecutionTrace stored inside
AgentState. It records node start/end events, execution durations, and
failures without maintaining any internal mutable state.

Responsibilities:
-----------------
- Start node execution spans.
- Complete node execution spans.
- Record failed node executions.
- Finalize execution traces.

This module DOES NOT:
---------------------
- Persist traces.
- Compute business metrics.
- Know about tickets, routing, or tools.
- Integrate with logging frameworks.

Architecture:
-------------
AgentState
    │
    └── ExecutionTrace
            │
            ├── NodeTrace
            ├── NodeTrace
            └── ...

Every graph node updates the shared ExecutionTrace through this utility.

Future Extensions:
------------------
Later milestones may extend NodeTrace with:
- LLM latency
- Token usage
- Retry count
- Provider metadata
- OpenTelemetry span IDs

without changing the public API.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.execution_trace import ExecutionTrace
from app.schemas.node_trace import NodeTrace


class ExecutionTracer:
    """
    Stateless utility for updating an ExecutionTrace.
    """

    @classmethod
    def start_node(
        cls,
        trace: ExecutionTrace,
        node_name: str,
    ) -> None:
        """
        Begin execution of a graph node.

        Args:
            trace:
                Execution trace being updated.

            node_name:
                Name of the LangGraph node.
        """

        trace.nodes.append(
            NodeTrace(
                node_name=node_name,
                started_at=datetime.now(UTC),
            )
        )

    @classmethod
    def end_node(
        cls,
        trace: ExecutionTrace,
        node_name: str,
    ) -> None:
        """
        Mark a node as successfully completed.
        """

        node = cls._find_running_node(trace, node_name)

        if node is None:
            return

        finished = datetime.now(UTC)

        node.finished_at = finished
        node.duration_ms = (
            finished - node.started_at
        ).total_seconds() * 1000

        node.status = "completed"

    @classmethod
    def fail_node(
        cls,
        trace: ExecutionTrace,
        node_name: str,
        error: Exception,
    ) -> None:
        """
        Mark a node as failed.
        """

        node = cls._find_running_node(trace, node_name)

        if node is None:
            return

        finished = datetime.now(UTC)

        node.finished_at = finished
        node.duration_ms = (
            finished - node.started_at
        ).total_seconds() * 1000

        node.status = "failed"
        node.error = f"{type(error).__name__}: {error}"

    @staticmethod
    def _find_running_node(
        trace: ExecutionTrace,
        node_name: str,
    ) -> NodeTrace | None:
        """
        Return the most recent running span for a node.

        Searching from the end supports future nested or repeated
        executions of the same node.
        """

        for node in reversed(trace.nodes):
            if (
                node.node_name == node_name
                and node.status == "running"
            ):
                return node

        return None