"""
app/llm/llm_service.py

Purpose:
--------
Provide a single entry point for executing Large Language Model (LLM)
inference requests.

This service is responsible for executing LLM requests while
automatically recording operational observability metrics such as
execution latency, token usage, estimated cost, and execution status.

Although the current implementation uses OpenAI as the underlying
provider, callers remain provider-agnostic. Future providers (Azure
OpenAI, Anthropic, Gemini, Ollama, etc.) can be integrated without
changing the calling code.

Responsibilities:
-----------------
- Execute LLM inference requests.
- Retrieve the configured LLM client.
- Measure inference latency.
- Record token usage.
- Record LLM execution metrics.
- Return the provider response.

This service DOES NOT:
----------------------
- Construct LLM clients.
- Build prompts.
- Perform routing decisions.
- Manage conversation history.
- Execute graph nodes.
- Store business metrics.

Architecture:
-------------
Agent / Node
      │
      ▼
LLMService
      │
      ├── Get configured provider client
      ├── Execute inference request
      ├── Measure execution latency
      ├── Record LLMMetrics
      └── Return provider response

Future Extensions:
------------------
Later milestones may extend this service with:

- Multi-provider support
- Retry policies
- Rate limiting
- Response caching
- Streaming responses
- Cost estimation
- Prompt version tracking
- Structured output validation
"""

from datetime import UTC, datetime
from typing import Any

from openai.types.responses import Response

from app.llm.openai_client import get_openai_client
from app.schemas.execution_trace import ExecutionTrace
from app.schemas.llm_metrics import LLMMetrics
from app.config.settings import settings
from app.llm.pricing import estimate_cost


class LLMService:
    """
    Execute LLM inference requests while automatically recording
    execution metrics.
    """

    PROVIDER = settings.llm_provider

    @classmethod
    def create_response(
        cls,
        *,
        model: str,
        input: str,
        instructions: str | None = None,
        execution_trace: ExecutionTrace | None = None,
        node_name: str | None = None,
        **kwargs,
    ) -> Response:
        """
        Execute an LLM inference request.

        Parameters
        ----------
        model:
            Model used for inference.

        input:
            User input supplied to the model.

        instructions:
            Optional system instructions.

        execution_trace:
            Execution trace used to record LLM metrics.

        node_name:
            Optional graph node responsible for this LLM invocation.

        kwargs:
            Additional keyword arguments forwarded directly to the
            provider SDK.

        Returns
        -------
        Response
            Provider response object.
        """

        client = get_openai_client()

        started_at = datetime.now(UTC)

        try:

            response = client.responses.create(
                model=model,
                input=input,
                instructions=instructions,
                **kwargs,
            )

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                response=response,
                success=True,
                node_name=node_name,
            )

            return response

        except Exception as exc:

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                success=False,
                error=str(exc),
                node_name=node_name,
            )

            raise

    @classmethod
    def create_chat_completion(
        cls,
        *,
        model: str,
        messages: list[dict[str, str]],
        execution_trace: ExecutionTrace | None = None,
        node_name: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute a chat completion request and record metrics.

        This is used by prompt-driven generation flows that already build
        chat-style message payloads.
        """

        client = get_openai_client()

        started_at = datetime.now(UTC)

        try:

            completion = client.chat.completions.create(
                model=model,
                messages=messages, # type: ignore
                **kwargs,
            )

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                response=completion,
                success=True,
                node_name=node_name,
            )

            return completion

        except Exception as exc:

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                success=False,
                error=str(exc),
                node_name=node_name,
            )

            raise

    @classmethod
    def parse_chat_completion(
        cls,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: type[Any],
        execution_trace: ExecutionTrace | None = None,
        node_name: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute a structured chat completion request and record metrics.

        This wraps OpenAI's beta chat completion parser so nodes can use
        Pydantic structured output without bypassing LLM observability.
        """

        client = get_openai_client()

        started_at = datetime.now(UTC)

        try:

            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages, # type: ignore
                response_format=response_format,
                **kwargs,
            )

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                response=completion,
                success=True,
                node_name=node_name,
            )

            return completion

        except Exception as exc:

            finished_at = datetime.now(UTC)

            cls._record_metrics(
                execution_trace=execution_trace,
                model=model,
                started_at=started_at,
                finished_at=finished_at,
                success=False,
                error=str(exc),
                node_name=node_name,
            )

            raise

    @classmethod
    def _record_metrics(
        cls,
        *,
        execution_trace: ExecutionTrace | None,
        model: str,
        started_at: datetime,
        finished_at: datetime,
        success: bool,
        response: Any | None = None,
        error: str | None = None,
        node_name: str | None = None,
    ) -> None:
        """
        Append one LLM metrics entry to the execution trace, if present.
        """

        if execution_trace is None:
            return

        prompt_tokens, completion_tokens, total_tokens = (
            cls._extract_token_usage(response)
        )

        execution_trace.llm_metrics.append(
            LLMMetrics(
                provider=cls.PROVIDER,
                model_name=model,
                node_name=node_name,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=(
                    finished_at - started_at
                ).total_seconds()
                * 1000,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimate_cost(
                    provider=cls.PROVIDER,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                ),
                success=success,
                error=error,
            )
        )

    @staticmethod
    def _extract_token_usage(
        response: Any | None,
    ) -> tuple[int | None, int | None, int | None]:
        """
        Return prompt, completion, and total tokens from provider response.

        OpenAI Responses objects expose input/output token names, while
        chat completion objects expose prompt/completion token names.
        """

        usage = getattr(response, "usage", None)

        if usage is None:
            return None, None, None

        prompt_tokens = (
            getattr(usage, "input_tokens", None)
            or getattr(usage, "prompt_tokens", None)
        )

        completion_tokens = (
            getattr(usage, "output_tokens", None)
            or getattr(usage, "completion_tokens", None)
        )

        total_tokens = getattr(usage, "total_tokens", None)

        if (
            total_tokens is None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = prompt_tokens + completion_tokens

        return prompt_tokens, completion_tokens, total_tokens
