"""
app/observability/tracing.py

Purpose:
--------
Provides a decorator that transparently instruments LangGraph nodes with
execution tracing.

The decorator measures node execution time without requiring any tracing
logic inside business nodes.

Responsibilities:
-----------------
- Start node timing.
- Complete node timing.
- Record failures.
- Leave node implementations unchanged.

This module DOES NOT:
---------------------
- Persist traces.
- Perform logging.
- Compute metrics.
- Modify business logic.

Architecture:
-------------
Original Node
      │
      ▼
 traced(node_name)
      │
      ▼
ExecutionTracer
      │
      ▼
ExecutionTrace
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from app.observability.tracer import ExecutionTracer
from app.schemas.agent_state import AgentState


def traced(
    node_name: str,
) -> Callable:  # type: ignore
    """
    Wrap a LangGraph node with automatic execution tracing.

    Args:
        node_name:
            Name recorded inside the ExecutionTrace.

    Returns:
        Decorated graph node.
    """

    def decorator(func: Callable):

        @wraps(func)
        def wrapper(state: AgentState):

            trace = state.execution_trace

            if trace is None:
                return func(state)

            ExecutionTracer.start_node(trace, node_name)

            try:
                result = func(state)

                # Use the trace from the returned state if available.
                if isinstance(result, AgentState):
                    trace = result.execution_trace or trace

                ExecutionTracer.end_node(
                    trace,
                    node_name,
                )

                return result

            except Exception as exc:
                ExecutionTracer.fail_node(
                    trace,
                    node_name,
                    exc,
                )

                raise

        return wrapper

    return decorator
