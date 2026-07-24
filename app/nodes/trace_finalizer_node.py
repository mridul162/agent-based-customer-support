"""
app/nodes/trace_finalizer_node.py

Purpose:
--------
Finalize the ExecutionTrace at the end of graph execution.

Responsibilities:
-----------------
- Complete total execution timing.
- Store finished_at.
- Calculate total_duration_ms.

Future milestones will extend this node to:
- Persist traces
- Send metrics
- Export telemetry
"""

from datetime import UTC, datetime

from app.schemas.agent_state import AgentState


def trace_finalizer_node(state: AgentState) -> AgentState:
    """
    Finalize execution timing.
    """

    if state.execution_trace is None:
        return state

    finished = datetime.now(UTC)

    state.execution_trace.finished_at = finished

    state.execution_trace.total_duration_ms = (
        finished - state.execution_trace.started_at
    ).total_seconds() * 1000

    return state