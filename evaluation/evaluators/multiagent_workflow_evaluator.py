from __future__ import annotations

from typing import Any

from evaluation.evaluators.base_evaluator import BaseEvaluator
from evaluation.evaluators.evaluation_result import (
    EvaluationExecutionResult,
    EvaluationFailure,
    EvaluationResult,
)


class MultiAgentWorkflowEvaluator(BaseEvaluator):
    """
    Evaluate the complete router_graph multi-agent workflow.
    """

    def _evaluate_case(
        self,
        execution_result: EvaluationExecutionResult,
    ) -> EvaluationResult:
        failures: list[EvaluationFailure] = []

        if execution_result.error is not None:
            failures.append(
                self.failure(
                    field="execution",
                    expected="No execution error",
                    observed=execution_result.error,
                    message="Runner reported an execution error.",
                )
            )
            return self.failed_result(
                execution_result=execution_result,
                failures=failures,
            )

        expected = execution_result.expected
        observed = execution_result.observed or {}

        self._check_equal(
            failures,
            field="agent_name",
            expected=expected.get("agent_name"),
            observed=self._observed_agent_name(observed),
        )
        self._check_equal(
            failures,
            field="tool_name",
            expected=expected.get("tool_name"),
            observed=observed.get("tool_used"),
        )
        self._check_equal(
            failures,
            field="needs_clarification",
            expected=expected.get("needs_clarification"),
            observed=observed.get("needs_clarification"),
        )
        self._check_equal(
            failures,
            field="needs_human",
            expected=expected.get("needs_human"),
            observed=observed.get("needs_human"),
        )

        if "ticket_created" in expected:
            self._check_equal(
                failures,
                field="ticket_created",
                expected=expected["ticket_created"],
                observed=bool(observed.get("ticket_id")),
            )

        if "escalated" in expected:
            metrics = self._trace_metrics(observed)
            self._check_equal(
                failures,
                field="escalated",
                expected=expected["escalated"],
                observed=metrics.get("escalated"),
            )

        self._check_arguments(
            failures=failures,
            expected=expected,
            observed=observed,
        )

        self._check_missing_arguments(
            failures=failures,
            expected=expected,
            observed=observed,
        )

        self._check_response_contains(
            failures=failures,
            expected=expected,
            observed=observed,
        )

        self._check_trace_health(
            failures=failures,
            expected=expected,
            observed=observed,
        )

        if failures:
            return self.failed_result(
                execution_result=execution_result,
                failures=failures,
            )

        return self.passed_result(execution_result=execution_result)

    def _check_equal(
        self,
        failures: list[EvaluationFailure],
        *,
        field: str,
        expected: Any,
        observed: Any,
    ) -> None:
        if expected != observed:
            failures.append(
                self.failure(
                    field=field,
                    expected=expected,
                    observed=observed,
                    message=f"{field} does not match expectation.",
                )
            )

    def _observed_agent_name(self, observed: dict[str, Any]) -> str | None:
        routing_decision = observed.get("routing_decision")

        if routing_decision is None:
            return None

        return routing_decision.get("agent_name")

    def _trace_metrics(self, observed: dict[str, Any]) -> dict[str, Any]:
        trace = observed.get("execution_trace") or {}
        return trace.get("metrics") or {}

    def _check_arguments(
        self,
        *,
        failures: list[EvaluationFailure],
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> None:
        expected_arguments = expected.get("arguments", {})
        extracted = observed.get("extracted_arguments") or {}
        observed_arguments = extracted.get("values", {})

        for argument_name, expected_value in expected_arguments.items():
            observed_value = observed_arguments.get(argument_name)
            if observed_value != expected_value:
                failures.append(
                    self.failure(
                        field=f"arguments.{argument_name}",
                        expected=expected_value,
                        observed=observed_value,
                        message=f"Incorrect extracted value for {argument_name}.",
                    )
                )

    def _check_missing_arguments(
        self,
        *,
        failures: list[EvaluationFailure],
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> None:
        expected_missing = expected.get("missing_arguments")

        if expected_missing is None:
            return

        observed_missing = observed.get("missing_arguments", [])

        if sorted(expected_missing) != sorted(observed_missing):
            failures.append(
                self.failure(
                    field="missing_arguments",
                    expected=expected_missing,
                    observed=observed_missing,
                    message="Missing argument list does not match expectation.",
                )
            )

    def _check_response_contains(
        self,
        *,
        failures: list[EvaluationFailure],
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> None:
        expected_terms = expected.get("response_contains", [])
        response = (observed.get("response") or "").lower()

        for term in expected_terms:
            if term.lower() not in response:
                failures.append(
                    self.failure(
                        field="response",
                        expected=f"contains {term}",
                        observed=observed.get("response"),
                        message="Response did not contain expected text.",
                    )
                )

    def _check_trace_health(
        self,
        *,
        failures: list[EvaluationFailure],
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> None:
        trace = observed.get("execution_trace")

        if trace is None:
            failures.append(
                self.failure(
                    field="execution_trace",
                    expected="trace present",
                    observed=None,
                    message="ExecutionTrace was not populated.",
                )
            )
            return

        if not trace.get("nodes"):
            failures.append(
                self.failure(
                    field="execution_trace.nodes",
                    expected="at least one traced node",
                    observed=[],
                    message="No node traces were recorded.",
                )
            )

        expected_tool = expected.get("tool_name")
        tool_metrics = trace.get("tool_metrics", [])

        if expected_tool is not None and not tool_metrics:
            failures.append(
                self.failure(
                    field="execution_trace.tool_metrics",
                    expected="tool metrics recorded",
                    observed=tool_metrics,
                    message="Expected tool metrics for a tool execution.",
                )
            )
