"""
app/schemas/llm_metrics.py

Purpose:
--------
Represents the execution metrics of a single Large Language Model (LLM)
invocation.

Unlike ExecutionMetrics, which summarizes the business outcome of an
entire customer request, LLMMetrics captures the operational details of
one LLM call, including execution timing, token usage, estimated cost,
and success or failure information.

This schema provides observability into AI model performance and serves
as the foundation for monitoring latency, token consumption, operational
cost, and provider reliability.

Responsibilities:
-----------------
- Record which LLM provider was used.
- Record which model generated the response.
- Record execution timing.
- Record token usage.
- Record estimated inference cost.
- Record whether execution succeeded.
- Record optional error information.

This schema DOES NOT:
---------------------
- Store customer messages.
- Store prompts or generated responses.
- Store retrieval context.
- Store business outcome metrics.
- Store graph execution history.
- Execute or validate LLM requests.

Architecture:
-------------
ExecutionTrace
    ├── NodeTrace (...)
    ├── ExecutionMetrics
    ├── ToolMetrics (...)
    └── LLMMetrics
            ├── provider
            ├── model_name
            ├── started_at
            ├── finished_at
            ├── duration_ms
            ├── prompt_tokens
            ├── completion_tokens
            ├── total_tokens
            ├── estimated_cost_usd
            ├── success
            └── error

Why keep LLMMetrics separate?
-----------------------------
ExecutionMetrics answers:

    "What business outcome did this request produce?"

ToolMetrics answers:

    "How did external tools perform?"

LLMMetrics answers:

    "How did the AI model perform?"

Separating these concerns enables independent monitoring of AI latency,
token usage, operational costs, and provider reliability without mixing
them with business analytics or graph execution details.

Future Extensions:
------------------
Later milestones may extend this schema with:

- temperature
- max_tokens
- top_p
- frequency_penalty
- presence_penalty
- stop_reason
- cached_tokens
- reasoning_tokens
- retry_count
- rate_limit_remaining
- request_id
- provider_response_id

without affecting the existing observability infrastructure.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class LLMMetrics(BaseModel):
    """
    Operational metrics for a single LLM invocation.
    """

    provider: str = Field(
        ...,
        description="Name of the LLM provider.",
    )

    model_name: str = Field(
        ...,
        description="Name of the model used for inference.",
    )

    node_name: str | None = Field(
        default=None,
        description="Graph node responsible for the LLM invocation.",
    )

    started_at: datetime = Field(
        ...,
        description="UTC timestamp when the LLM request began.",
    )

    finished_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the LLM request completed.",
    )

    duration_ms: float | None = Field(
        default=None,
        ge=0,
        description="LLM execution duration in milliseconds.",
    )

    prompt_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Number of input (prompt) tokens consumed.",
    )

    completion_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Number of output (completion) tokens generated.",
    )

    total_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Total number of tokens consumed.",
    )

    estimated_cost_usd: float | None = Field(
        default=None,
        ge=0,
        description="Estimated inference cost in USD.",
    )

    success: bool = Field(
        default=False,
        description="Whether the LLM invocation completed successfully.",
    )

    error: str | None = Field(
        default=None,
        description="Error message if the LLM invocation failed.",
    )
