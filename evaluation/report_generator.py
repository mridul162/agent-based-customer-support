"""
tests/evaluation/report_generator.py

Purpose
-------
Generate a human-readable evaluation report.

Responsibilities
----------------
- Format evaluation summary statistics.
- Display failed evaluation cases.
- Produce a report suitable for console output,
  log files, or CI pipelines.

This module DOES NOT:
---------------------
- Execute evaluation cases.
- Compare expected vs observed values.
- Compute evaluation metrics.

Architecture
------------
EvaluationSummary
        │
        ▼
 ReportGenerator
        │
        ▼
     Text Report
"""

from __future__ import annotations

from evaluation.evaluators.evaluation_result import (
    EvaluationSummary,
)


class ReportGenerator:
    """
    Generates a human-readable evaluation report.
    """

    _SEPARATOR = "=" * 70
    _SUB_SEPARATOR = "-" * 70

    def generate(
        self,
        summary: EvaluationSummary,
        *,
        title: str = "Evaluation Report",
    ) -> str:
        """
        Generate a formatted evaluation report.

        Parameters
        ----------
        summary:
            Aggregate evaluation results.

        title:
            Report title.

        Returns
        -------
        str
            Formatted report.
        """

        lines: list[str] = []

        # ==============================================================
        # Header
        # ==============================================================

        lines.append(self._SEPARATOR)
        lines.append(title)
        lines.append(self._SEPARATOR)

        lines.append("")

        # ==============================================================
        # Summary
        # ==============================================================

        lines.append("Summary")
        lines.append(self._SUB_SEPARATOR)

        lines.append(f"Total Cases       : {summary.total_cases}")
        lines.append(f"Passed            : {summary.passed_cases}")
        lines.append(f"Failed            : {summary.failed_cases}")
        lines.append(f"Accuracy          : {summary.accuracy:.2f}%")
        lines.append(
            f"Average Latency   : {summary.average_latency_ms:.2f} ms"
        )
        lines.append(
            f"Execution Errors  : {summary.execution_errors}"
        )

        # ==============================================================
        # Failed Cases
        # ==============================================================

        failed_results = [
            result
            for result in summary.results
            if not result.passed
        ]

        if failed_results:

            lines.append("")
            lines.append("Failed Cases")
            lines.append(self._SUB_SEPARATOR)

            for result in failed_results:

                lines.append(f"Case ID : {result.case_id}")

                if result.execution_error is not None:
                    lines.append(
                        f"Execution Error : {result.execution_error}"
                    )

                for failure in result.failures:

                    lines.append(
                        f"  Field    : {failure.field}"
                    )
                    lines.append(
                        f"  Expected : {failure.expected}"
                    )
                    lines.append(
                        f"  Observed : {failure.observed}"
                    )
                    lines.append(
                        f"  Reason   : {failure.message}"
                    )
                    lines.append("")

                lines.append(self._SUB_SEPARATOR)

        else:

            lines.append("")
            lines.append("No failed evaluation cases.")

        return "\n".join(lines)