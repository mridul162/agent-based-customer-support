from __future__ import annotations

import time
from typing import Any

from evaluation.evaluators.evaluation_result import EvaluationExecutionResult
from evaluation.runners.base_runner import BaseRunner


class MultiAgentWorkflowRunner(BaseRunner):
    """
    Execute multi-agent workflow evaluation cases through an executor.
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
            state = self.executor.execute(
                customer_id=input_data["customer_id"],
                message=input_data["message"],
            )

            latency_ms = (time.perf_counter() - start) * 1000

            observed = state.model_dump()

            return EvaluationExecutionResult(
                case_id=case["id"],
                description=case.get("description"),
                tags=case.get("tags", []),
                input=input_data,
                expected=case["expected"],
                observed=observed,
                latency_ms=latency_ms,
                error=None,
            )

        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000

            return EvaluationExecutionResult(
                case_id=case["id"],
                description=case.get("description"),
                tags=case.get("tags", []),
                input=input_data,
                expected=case["expected"],
                observed=None,
                latency_ms=latency_ms,
                error=str(exc),
            )
