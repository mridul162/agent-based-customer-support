"""
tests/evaluation/evaluators/tool_selection_evaluator.py

Purpose
-------
Evaluates whether the support agent selected the correct tool for
each evaluation case.

Responsibilities
----------------
- Compare the expected tool with the observed tool.
- Validate clarification behaviour.
- Validate extracted arguments.
- Detect execution errors.
- Produce EvaluationResult objects.

This evaluator DOES NOT:
------------------------
- Execute the support agent.
- Compute aggregate metrics.
- Generate reports.
- Judge response quality.

Architecture
------------
EvaluationExecutionResult
            │
            ▼
ToolSelectionEvaluator
            │
            ▼
EvaluationResult
"""

from __future__ import annotations

from evaluation.evaluators.base_evaluator import BaseEvaluator
from evaluation.evaluators.evaluation_result import (
    EvaluationExecutionResult,
    EvaluationFailure,
    EvaluationResult,
)


class ToolSelectionEvaluator(BaseEvaluator):
    """
    Evaluates tool-selection correctness.

    Validation order:

        1. Execution errors
        2. Selected tool
        3. Clarification requirement
        4. Tool arguments
    """

    def _evaluate_case(
        self,
        execution_result: EvaluationExecutionResult,
    ) -> EvaluationResult:

        failures: list[EvaluationFailure] = []

        # ----------------------------------------------------------
        # Execution error
        # ----------------------------------------------------------

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

        # ----------------------------------------------------------
        # Tool selection
        # ----------------------------------------------------------

        expected_tool = expected.get("tool_name")
        observed_tool = observed.get("tool_used")

        if expected_tool != observed_tool:
            failures.append(
                self.failure(
                    field="tool_name",
                    expected=expected_tool,
                    observed=observed_tool,
                    message="Incorrect tool selected.",
                )
            )

        # ----------------------------------------------------------
        # Clarification behaviour
        # ----------------------------------------------------------

        expected_clarification = expected.get(
            "needs_clarification"
        )

        observed_clarification = observed.get(
            "needs_clarification"
        )

        if (
            expected_clarification is not None
            and expected_clarification != observed_clarification
        ):
            failures.append(
                self.failure(
                    field="needs_clarification",
                    expected=expected_clarification,
                    observed=observed_clarification,
                    message="Clarification behaviour does not match expectation.",
                )
            )

        # ----------------------------------------------------------
        # Tool arguments
        # ----------------------------------------------------------

        expected_arguments = expected.get("arguments", {})

        observed_arguments = observed.get("arguments", {})

        for argument_name, expected_value in expected_arguments.items():

            observed_value = observed_arguments.get(argument_name)

            if observed_value != expected_value:
                failures.append(
                    self.failure(
                        field=f"arguments.{argument_name}",
                        expected=expected_value,
                        observed=observed_value,
                        message=f"Incorrect value for '{argument_name}'.",
                    )
                )

        # ----------------------------------------------------------
        # Build final result
        # ----------------------------------------------------------

        if failures:
            return self.failed_result(
                execution_result=execution_result,
                failures=failures,
            )

        return self.passed_result(
            execution_result=execution_result,
        )