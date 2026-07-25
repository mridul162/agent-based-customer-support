"""
tests/validate_llm_metrics.py

Purpose:
--------
Validate Milestone 14.5 (LLM Execution Metrics).

This script executes a complete graph run that invokes an LLM and
verifies that LLMMetrics are recorded correctly inside the
ExecutionTrace.

Validation:
-----------
- ExecutionTrace exists
- LLM metrics recorded
- Exactly one LLM invocation recorded
- Provider recorded
- Model recorded
- Start timestamp recorded
- Finish timestamp recorded
- Duration recorded
- Token usage recorded (if available)
- LLM execution succeeded
- No execution error

Run:
----
python -m tests.validate_llm_metrics
"""

from uuid import uuid4

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState


def check(condition: bool, message: str) -> None:
    """Print PASS/FAIL for a validation check."""

    if condition:
        print(f"  ✅ PASS   {message}")
    else:
        print(f"  ❌ FAIL   {message}")


def main() -> None:

    print("=" * 60)
    print("  Milestone 14.5 — LLM Execution Metrics")
    print("=" * 60)

    print("\nInitialising database...")
    init_db()

    print("\n[Scenario 1] Refund request\n")

    state = AgentState(
        request_id=str(uuid4()),
        customer_id="customer-001",
        message="I received a damaged product and want a refund.",
    )

    result = router_graph.invoke(state)

    state = (
        result
        if isinstance(result, AgentState)
        else AgentState(**result)
    )    

    trace = state.execution_trace

    check(trace is not None, "ExecutionTrace exists")

    if trace is None:
        return

    check(
        len(trace.llm_metrics) > 0,
        "LLM metrics recorded",
    )

    check(
        len(trace.llm_metrics) == 1,
        "Exactly one LLM invocation recorded",
    )

    if not trace.llm_metrics:
        return

    llm = trace.llm_metrics[0]

    check(
        llm.provider is not None,
        "Provider recorded",
    )

    check(
        llm.model_name is not None,
        "Model recorded",
    )

    check(
        llm.started_at is not None,
        "Start timestamp recorded",
    )

    check(
        llm.finished_at is not None,
        "Finish timestamp recorded",
    )

    check(
        llm.duration_ms is not None
        and llm.duration_ms >= 0,
        "Execution duration recorded",
    )

    if (
        llm.prompt_tokens is not None
        and llm.completion_tokens is not None
        and llm.total_tokens is not None
    ):

        check(
            llm.total_tokens
            == llm.prompt_tokens + llm.completion_tokens,
            "Total token count correct",
        )


    else:

        print("  ⚠️  Token usage unavailable from provider response")

    check(
        llm.success,
        "LLM execution succeeded",
    )

    check(
        llm.error is None,
        "No execution error",
    )

    check(
    llm.estimated_cost_usd is not None,
    "Estimated cost calculated",
    )

    print("\nLLM Metrics")
    print("-" * 60)
    print(f"Provider             : {llm.provider}")
    print(f"Model                : {llm.model_name}")
    print(f"Success              : {llm.success}")
    print(f"Duration (ms)        : {llm.duration_ms:.2f}")

    print(f"Prompt Tokens        : {llm.prompt_tokens}")
    print(f"Completion Tokens    : {llm.completion_tokens}")
    print(f"Total Tokens         : {llm.total_tokens}")
    print(f"Estimated Cost (USD) : ${llm.estimated_cost_usd:.8f}")

    if llm.error:
        print(f"Error                : {llm.error}")
    else:
        print("Error                : None")

    print("\n" + "=" * 60)
    print("  LLM Execution Metrics           ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()