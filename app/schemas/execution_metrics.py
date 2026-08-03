"""
app/schemas/execution_metrics.py

Purpose:
--------
Represents the high-level execution outcome of a single customer request.

Unlike ExecutionTrace, which records the chronological execution timeline,
ExecutionMetrics summarizes the business-level results of the request.
These metrics provide a concise overview for observability, analytics,
dashboards, and future reporting.

Responsibilities:
-----------------
- Record which specialist agent handled the request.
- Record which tool was executed.
- Indicate whether clarification was requested.
- Indicate whether the conversation was escalated.
- Indicate whether a support ticket was created.
- Store the total request latency.

This schema DOES NOT:
---------------------
- Store node execution history.
- Store timestamps for individual nodes.
- Record token usage or LLM provider metadata.
- Store customer messages or responses.
- Contain execution logic.

Architecture:
-------------
ExecutionTrace
    ├── NodeTrace (...)
    ├── NodeTrace (...)
    ├── ...
    └── ExecutionMetrics
            ├── agent_name
            ├── tool_used
            ├── clarification_requested
            ├── escalated
            ├── ticket_created
            └── total_latency_ms

Why keep metrics separate from NodeTrace?
-----------------------------------------
NodeTrace answers:

    "How did the graph execute?"

ExecutionMetrics answers:

    "What business outcome did the execution produce?"

Keeping these concerns separate allows dashboards, analytics, and reporting
to consume a compact request summary without traversing the full execution
timeline.

Future Extensions:
------------------
Later milestones may extend this schema with:
- prompt_tokens
- completion_tokens
- total_tokens
- model_name
- provider_name
- estimated_cost
- retrieval_count
- retrieved_documents
- retry_count
- confidence_score

without affecting existing tracing infrastructure.
"""

from pydantic import BaseModel, Field


class ExecutionMetrics(BaseModel):
    """
    Business-level summary of a completed request execution.
    """

    agent_name: str | None = Field(
        default=None,
        description="Specialist agent selected to handle the request.",
    )

    tool_used: str | None = Field(
        default=None,
        description="Tool executed during request processing.",
    )

    clarification_requested: bool = Field(
        default=False,
        description="Whether additional information was requested from the customer.",
    )

    escalated: bool = Field(
        default=False,
        description="Whether the conversation was escalated for human support.",
    )

    ticket_created: bool = Field(
        default=False,
        description="Whether a support ticket was successfully created.",
    )

    total_latency_ms: float | None = Field(
        default=None,
        ge=0,
        description="Total end-to-end request latency in milliseconds.",
    )
