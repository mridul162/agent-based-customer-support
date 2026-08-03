"""
app/schemas/tool_metrics.py

Purpose:
--------
Represents the execution metrics of a single tool invocation.

Unlike ExecutionMetrics, which summarizes the business outcome of an
entire customer request, ToolMetrics captures the operational details
of one tool execution, including timing, success, and failure
information.

This schema provides observability into external business operations
performed by the agent, such as ticket creation, ticket lookup, or
future integrations with payment gateways, CRMs, or knowledge systems.

Responsibilities:
-----------------
- Record which tool was executed.
- Record tool execution timing.
- Record whether execution succeeded.
- Record optional error information.
- Remain independent of business logic.

This schema DOES NOT:
---------------------
- Store customer messages.
- Store tool inputs or outputs.
- Record graph node execution history.
- Store request-level business metrics.
- Execute or validate tool logic.

Architecture:
-------------
ExecutionTrace
    ├── NodeTrace (...)
    ├── NodeTrace (...)
    ├── ExecutionMetrics
    └── ToolMetrics
            ├── tool_name
            ├── started_at
            ├── finished_at
            ├── duration_ms
            ├── success
            └── error

Why keep ToolMetrics separate from ExecutionMetrics?
----------------------------------------------------
ExecutionMetrics answers:

    "What business outcome did this request produce?"

ToolMetrics answers:

    "How did the tool execution perform?"

Separating these concerns allows operational dashboards to analyze tool
latency, reliability, and failures independently from business-level
analytics.

Future Extensions:
------------------
Later milestones may extend this schema with:
- retry_count
- provider_name
- api_endpoint
- http_status
- request_size
- response_size
- cache_hit
- rate_limit_remaining
- estimated_cost

without affecting existing observability infrastructure.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ToolExecutionStatus = Literal[
    "success",
    "failed",
]


class ToolMetrics(BaseModel):
    """
    Operational metrics for a single tool execution.
    """

    tool_name: str = Field(
        ...,
        description="Name of the executed tool.",
    )

    started_at: datetime = Field(
        ...,
        description="UTC timestamp when tool execution began.",
    )

    finished_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when tool execution completed.",
    )

    duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="Tool execution duration in milliseconds.",
    )

    success: bool = Field(
        default=False,
        description="Whether the tool completed successfully.",
    )

    status: ToolExecutionStatus = Field(
        default="success",
        description="Final execution status of the tool.",
    )

    error: str | None = Field(
        default=None,
        description="Error message if tool execution failed.",
    )
