"""
tests/evaluation/metrics.py

Purpose
-------
Compute aggregate evaluation metrics from evaluation results.

Responsibilities
----------------
- Count passed and failed cases.
- Calculate accuracy.
- Calculate average latency.
- Count execution errors.
- Produce an EvaluationSummary.

This module DOES NOT:
---------------------
- Execute evaluation cases.
- Compare expected vs observed outputs.
- Generate reports.

Architecture
------------
EvaluationResult[]
        │
        ▼
EvaluationMetrics
        │
        ▼
EvaluationSummary
"""

from __future__ import annotations

from evaluation.evaluators.evaluation_result import (
    EvaluationResult,
    EvaluationSummary,
)


class EvaluationMetrics:
    """
    Computes aggregate metrics for an evaluation run.

    This class is intentionally generic and independent of any
    specific evaluator (tool selection, retrieval, workflow, etc.).
    """

    def compute(
        self,
        results: list[EvaluationResult],
    ) -> EvaluationSummary:
        """
        Compute aggregate evaluation metrics.

        Parameters
        ----------
        results:
            Evaluation results produced by an Evaluator.

        Returns
        -------
        EvaluationSummary
        """

        total_cases = len(results)

        passed_cases = sum(
            result.passed
            for result in results
        )

        failed_cases = total_cases - passed_cases

        accuracy = (
            (passed_cases / total_cases) * 100
            if total_cases > 0
            else 0.0
        )

        average_latency_ms = (
            sum(result.latency_ms for result in results) / total_cases
            if total_cases > 0
            else 0.0
        )

        execution_errors = sum(
            result.execution_error is not None
            for result in results
        )

        return EvaluationSummary(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            accuracy=accuracy,
            average_latency_ms=average_latency_ms,
            execution_errors=execution_errors,
            results=results,
        )