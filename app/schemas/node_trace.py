"""
app/schemas/node_trace.py

Purpose:
--------
Represents the execution of a single LangGraph node.

Each time a node begins execution, a NodeTrace is created.
When the node finishes, timing information is recorded.

Responsibilities:
-----------------
- Store node execution timing.
- Record execution status.
- Store optional error information.
- Remain independent of business logic.

This schema DOES NOT:
---------------------
- Store routing decisions.
- Store ticket IDs.
- Store tool outputs.
- Store customer responses.
- Aggregate multiple nodes.

Architecture:
-------------
ExecutionTrace
    ├── NodeTrace (memory_loader_node)
    ├── NodeTrace (router_node)
    ├── NodeTrace (agent_dispatch_node)
    └── ...

Future Extensions:
------------------
Later milestones may extend this schema with:
- token usage
- LLM latency
- retries
- provider metadata

without affecting existing code.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NodeStatus = Literal[
    "running",
    "completed",
    "failed",
]


class NodeTrace(BaseModel):
    """
    Execution record for one graph node.
    """

    node_name: str = Field(
        ...,
        description="Name of the executed graph node.",
    )

    started_at: datetime = Field(
        ...,
        description="UTC timestamp when execution began.",
    )

    finished_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when execution completed.",
    )

    duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="Execution duration in milliseconds.",
    )

    status: NodeStatus = Field(
        default="running",
        description="Current execution state.",
    )

    error: str | None = Field(
        default=None,
        description="Error message if execution failed.",
    )
