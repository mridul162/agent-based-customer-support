from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from evaluation.evaluators.evaluation_result import (
    EvaluationExecutionResult,
)


class BaseRunner(ABC):
    """
    Base class for all evaluation runners.

    Responsibilities
    ----------------
    - Load evaluation datasets.
    - Execute evaluation cases.
    - Collect raw execution observations.

    This class DOES NOT:
    --------------------
    - Evaluate correctness.
    - Calculate metrics.
    - Generate reports.
    """

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)

    def load_dataset(self) -> list[dict[str, Any]]:
        with self.dataset_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def run(self) -> list[EvaluationExecutionResult]:
        """
        Execute every evaluation case.
        """

        dataset = self.load_dataset()

        results: list[EvaluationExecutionResult] = []

        for case in dataset:
            results.append(self.run_case(case))

        return results

    @abstractmethod
    def run_case(
        self,
        case: dict[str, Any],
    ) -> EvaluationExecutionResult:
        """
        Execute one evaluation case.

        Returns
        -------
        EvaluationExecutionResult
            Raw execution observation.
        """
        ...
