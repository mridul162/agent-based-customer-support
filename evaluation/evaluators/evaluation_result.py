"""
tests/evaluation/evaluators/evaluation_result.py

Purpose
-------
Defines the data contracts used by the evaluation framework.

Responsibilities
----------------
- Represent raw execution results from evaluation runners.
- Represent evaluated results after comparison.
- Provide a stable contract shared by runners, evaluators,
  metrics, and report generators.

This module DOES NOT:
---------------------
- Execute evaluation cases.
- Compare expected vs observed outputs.
- Compute metrics.
- Generate reports.

Architecture
------------
                Runner
                   │
                   ▼
        EvaluationExecutionResult
                   │
                   ▼
              Evaluator
                   │
                   ▼
          EvaluationResult
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    Metrics             Report Generator
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Raw execution result
# ============================================================================


class EvaluationExecutionResult(BaseModel):
    """
    Raw output produced by an EvaluationRunner.

    This model captures what actually happened during execution.

    No correctness is implied here.
    """

    case_id: str = Field(..., description="Unique identifier of the evaluation case.")

    description: str | None = Field(
        default=None, description="Human-readable description of the evaluation case."
    )

    tags: list[str] = Field(
        default_factory=list, description="Dataset tags describing the evaluation case."
    )

    input: dict[str, Any] = Field(
        default_factory=dict, description="Input used to execute the evaluation case."
    )

    expected: dict[str, Any] = Field(
        ..., description="Expected values defined by the evaluation dataset."
    )

    observed: dict[str, Any] | None = Field(
        default=None, description="Actual output returned by the application."
    )

    latency_ms: float = Field(
        ..., ge=0, description="Execution latency in milliseconds."
    )

    error: str | None = Field(
        default=None, description="Unhandled execution error, if any."
    )


# ============================================================================
# Individual evaluation failure
# ============================================================================


class EvaluationFailure(BaseModel):
    """
    Represents one failed evaluation assertion.
    """

    field: str = Field(..., description="Field that failed validation.")

    expected: Any = Field(..., description="Expected value.")

    observed: Any = Field(..., description="Observed value.")

    message: str = Field(..., description="Human-readable failure description.")


# ============================================================================
# Final evaluation result
# ============================================================================


class EvaluationResult(BaseModel):
    """
    Result after evaluating one execution result.

    Produced by Evaluators.
    Consumed by Metrics and Reports.
    """

    case_id: str

    description: str | None = None

    tags: list[str] = Field(default_factory=list)

    input: dict[str, Any] = Field(default_factory=dict)

    passed: bool

    latency_ms: float

    expected: dict[str, Any] = Field(default_factory=dict)

    observed: dict[str, Any] | None = None

    failures: list[EvaluationFailure] = Field(default_factory=list)

    execution_error: str | None = None


# ============================================================================
# Evaluation summary
# ============================================================================


class EvaluationSummary(BaseModel):
    """
    Aggregated evaluation results.

    Produced by Metrics.
    Consumed by ReportGenerator.
    """

    total_cases: int

    passed_cases: int

    failed_cases: int

    accuracy: float

    average_latency_ms: float

    execution_errors: int

    results: list[EvaluationResult]
