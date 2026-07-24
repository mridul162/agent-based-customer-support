"""
app/nodes/trace_initializer_node.py

Purpose:
--------
Initialize execution tracing for the current graph invocation.

This node creates an ExecutionTracer, starts a new ExecutionTrace,
and stores the trace inside AgentState.

Responsibilities:
-----------------
- Create a new ExecutionTracer.
- Initialize ExecutionTrace.
- Attach ExecutionTrace to AgentState.

This node DOES NOT:
-------------------
- Record node timings.
- Persist traces.
- Compute metrics.
- Perform analytics.

Architecture:
-------------
START
  ↓
trace_initializer_node
  ↓
memory_loader_node
  ↓
...
"""

from app.observability.tracer import ExecutionTracer
from app.schemas.agent_state import AgentState
from datetime import UTC, datetime
from app.schemas.execution_trace import ExecutionTrace


def trace_initializer_node(state: AgentState) -> AgentState:
    """
    Create the execution trace for the current request.
    """

    state.execution_trace = ExecutionTrace(
        request_id=state.request_id, # type: ignore
        customer_id=state.customer_id,
        started_at=datetime.now(UTC),
    )

    return state