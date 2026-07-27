"""
tests/evaluation/evaluators/base_evaluator.py

Purpose
-------
Provides the abstract base class for all evaluation components.

Responsibilities
----------------
- Define the evaluation workflow.
- Iterate over execution results.
- Collect evaluation results.
- Delegate comparison logic to subclasses.

This module DOES NOT:
---------------------
- Know anything about tool selection.
- Know anything about retrieval quality.
- Compute metrics.
- Generate reports.

Architecture
------------

EvaluationExecutionResult
            │
            ▼
      BaseEvaluator
            │
            ▼
   _evaluate_case(...)   ← implemented by subclasses
            │
            ▼
    EvaluationResult
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from evaluation.evaluators.evaluation_result import (
    EvaluationExecutionResult,
    EvaluationFailure,
    EvaluationResult,
)


class BaseEvaluator(ABC):
    """
    Base class for all evaluators.

    Subclasses implement the comparison logic for one evaluation type
    (tool selection, retrieval, workflow, etc.).

    This class owns the evaluation workflow while subclasses own the
    domain-specific validation rules.
    """

    def evaluate(
        self,
        execution_results: list[EvaluationExecutionResult],
    ) -> list[EvaluationResult]:
        """
        Evaluate every execution result.

        Parameters
        ----------
        execution_results:
            Raw outputs produced by an EvaluationRunner.

        Returns
        -------
        list[EvaluationResult]
            One evaluation result per execution result.
        """

        results: list[EvaluationResult] = []

        for execution_result in execution_results:
            results.append(
                self._evaluate_case(execution_result)
            )

        return results

    @abstractmethod
    def _evaluate_case(
        self,
        execution_result: EvaluationExecutionResult,
    ) -> EvaluationResult:
        """
        Evaluate a single execution result.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def failure(
        *,
        field: str,
        expected,
        observed,
        message: str,
    ) -> EvaluationFailure:
        """
        Create a standardized evaluation failure.
        """

        return EvaluationFailure(
            field=field,
            expected=expected,
            observed=observed,
            message=message,
        )

    @staticmethod
    def passed_result(
        *,
        execution_result: EvaluationExecutionResult,
    ) -> EvaluationResult:
        """
        Construct a successful evaluation result.
        """

        return EvaluationResult(
            case_id=execution_result.case_id,
            passed=True,
            latency_ms=execution_result.latency_ms,
            failures=[],
            execution_error=execution_result.error,
        )

    @staticmethod
    def failed_result(
        *,
        execution_result: EvaluationExecutionResult,
        failures: list[EvaluationFailure],
    ) -> EvaluationResult:
        """
        Construct a failed evaluation result.
        """

        return EvaluationResult(
            case_id=execution_result.case_id,
            passed=False,
            latency_ms=execution_result.latency_ms,
            failures=failures,
            execution_error=execution_result.error,
        )