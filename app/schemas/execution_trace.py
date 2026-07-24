"""
app/schemas/execution_trace.py

Purpose:
--------
Represents the complete execution timeline of a single customer request.

An ExecutionTrace is created at the beginning of graph execution
and accumulates NodeTrace objects as each node executes.

Responsibilities:
-----------------
- Identify the request being traced.
- Store request timing.
- Aggregate node execution traces.
- Compute total execution duration.

This schema DOES NOT:
---------------------
- Store routing decisions.
- Store ticket information.
- Store evaluation metrics.
- Store customer-facing responses.

Architecture:
-------------
HTTP Request
      │
      ▼
ExecutionTrace
      │
      ├── NodeTrace
      ├── NodeTrace
      ├── NodeTrace
      └── NodeTrace

Later Milestones:
-----------------
ExecutionMetrics
EvaluationReport
Analytics Dashboard

will consume ExecutionTrace without modifying it.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.node_trace import NodeTrace


class ExecutionTrace(BaseModel):
    """
    Timeline of one complete graph execution.
    """

    request_id: str = Field(
        ...,
        description="Unique request identifier.",
    )

    customer_id: str = Field(
        ...,
        description="Customer associated with this execution.",
    )

    started_at: datetime = Field(
        ...,
        description="UTC timestamp when graph execution began.",
    )

    finished_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when graph execution completed.",
    )

    total_duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="Total graph execution time in milliseconds.",
    )

    nodes: list[NodeTrace] = Field(
        default_factory=list,
        description="Ordered list of executed graph nodes.",
    )