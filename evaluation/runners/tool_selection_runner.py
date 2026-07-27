from __future__ import annotations

import time
from typing import Any
from unittest import result

from evaluation.runners.base_runner import BaseRunner
from evaluation.evaluators.evaluation_result import (
    EvaluationExecutionResult,
)


class ToolSelectionRunner(BaseRunner):
    """
    Executes tool selection evaluation cases.

    Produces raw observations for later evaluation.
    """

    def __init__(
        self,
        dataset_path: str,
        executor,
    ):
        super().__init__(dataset_path)

        self.executor = executor

    def run_case(
        self,
        case: dict[str, Any],
    ) -> EvaluationExecutionResult:

        input_data = case["input"]

        start = time.perf_counter()

        try:

            response = self.executor.execute(
                customer_id=input_data["customer_id"],
                message=input_data["message"],
            )

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            return EvaluationExecutionResult(
                case_id=case["id"],
                expected=case["expected"],
                observed=response.model_dump(),
                latency_ms=latency_ms,
                error=None,
            )

        except Exception as exc:

            latency_ms = (
                time.perf_counter() - start
            ) * 1000

            return EvaluationExecutionResult(
                case_id=case["id"],
                expected=case["expected"],
                observed=None,
                latency_ms=latency_ms,
                error=str(exc),
            )