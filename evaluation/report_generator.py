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

from collections import Counter
from typing import Any

from evaluation.evaluators.evaluation_result import (
    EvaluationResult,
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
        lines.append(f"Average Latency   : {summary.average_latency_ms:.2f} ms")
        lines.append(f"Execution Errors  : {summary.execution_errors}")

        # ==============================================================
        # Individual Cases
        # ==============================================================

        lines.append("")
        lines.append("Evaluated Cases")
        lines.append(self._SUB_SEPARATOR)

        for result in summary.results:
            lines.extend(self._format_case_result(result))
            lines.append(self._SUB_SEPARATOR)

        # ==============================================================
        # Detailed Summary
        # ==============================================================

        lines.append("")
        lines.append("Detailed Summary")
        lines.append(self._SUB_SEPARATOR)
        lines.extend(self._format_detailed_summary(summary))

        # ==============================================================
        # Failed Cases
        # ==============================================================

        failed_results = [result for result in summary.results if not result.passed]

        if failed_results:
            lines.append("")
            lines.append("Failed Cases")
            lines.append(self._SUB_SEPARATOR)

            for result in failed_results:
                lines.append(f"Case ID : {result.case_id}")

                if result.execution_error is not None:
                    lines.append(f"Execution Error : {result.execution_error}")

                for failure in result.failures:
                    lines.append(f"  Field    : {failure.field}")
                    lines.append(f"  Expected : {failure.expected}")
                    lines.append(f"  Observed : {failure.observed}")
                    lines.append(f"  Reason   : {failure.message}")
                    lines.append("")

                lines.append(self._SUB_SEPARATOR)

        else:
            lines.append("")
            lines.append("No failed evaluation cases.")

        return self._console_safe("\n".join(lines))

    def _format_case_result(
        self,
        result: EvaluationResult,
    ) -> list[str]:
        lines: list[str] = []
        status = "PASS" if result.passed else "FAIL"

        lines.append(f"Case ID           : {result.case_id}")
        lines.append(f"Status            : {status}")

        if result.description:
            lines.append(f"Description       : {result.description}")

        if result.tags:
            lines.append(f"Tags              : {', '.join(result.tags)}")

        customer_id = result.input.get("customer_id")
        message = result.input.get("message")

        if customer_id is not None:
            lines.append(f"Customer ID       : {customer_id}")

        if message is not None:
            lines.append(f"Message           : {message}")

        lines.append(f"Latency           : {result.latency_ms:.2f} ms")

        if result.execution_error is not None:
            lines.append(f"Execution Error   : {result.execution_error}")

        lines.append("Checks")
        for key, expected_value in result.expected.items():
            observed_value = self._observed_value(
                observed=result.observed,
                key=key,
                expected_value=expected_value,
            )
            lines.append(
                f"  {key}: expected={expected_value} | observed={observed_value}"
            )

        if result.failures:
            lines.append("Failures")
            for failure in result.failures:
                lines.append(f"  {failure.field}: {failure.message}")

        observed_summary = self._observed_summary(result.observed)
        if observed_summary:
            lines.append("Observed Workflow")
            for key, value in observed_summary.items():
                lines.append(f"  {key}: {value}")

        return lines

    def _format_detailed_summary(
        self,
        summary: EvaluationSummary,
    ) -> list[str]:
        results = summary.results
        lines: list[str] = []

        agent_counts: Counter[str] = Counter()
        tool_counts: Counter[str] = Counter()
        tag_counts: Counter[str] = Counter()
        check_counts: Counter[str] = Counter()
        failed_check_counts: Counter[str] = Counter()

        clarification_count = 0
        escalation_count = 0
        traced_cases = 0
        tool_metric_count = 0
        llm_metric_count = 0
        total_trace_nodes = 0

        for result in results:
            observed = result.observed or {}
            observed_summary = self._observed_summary(result.observed)
            agent = observed_summary.get("agent") or "none"
            tool_used = observed_summary.get("tool_used") or "none"

            agent_counts[str(agent)] += 1
            tool_counts[str(tool_used)] += 1
            tag_counts.update(result.tags)
            check_counts.update(result.expected.keys())
            failed_check_counts.update(failure.field for failure in result.failures)

            if observed.get("needs_clarification"):
                clarification_count += 1

            if observed.get("needs_human"):
                escalation_count += 1

            trace = observed.get("execution_trace") or {}
            if trace:
                traced_cases += 1
                total_trace_nodes += len(trace.get("nodes") or [])
                tool_metric_count += len(trace.get("tool_metrics") or [])
                llm_metric_count += len(trace.get("llm_metrics") or [])

        lines.append("Result Breakdown")
        lines.append(f"  Passed cases        : {summary.passed_cases}")
        lines.append(f"  Failed cases        : {summary.failed_cases}")
        lines.append(f"  Execution errors    : {summary.execution_errors}")
        lines.append(f"  Clarification cases : {clarification_count}")
        lines.append(f"  Human escalations   : {escalation_count}")

        lines.append("")
        lines.append("Coverage By Agent")
        lines.extend(self._format_counter(agent_counts))

        lines.append("")
        lines.append("Coverage By Tool Used")
        lines.extend(self._format_counter(tool_counts))

        lines.append("")
        lines.append("Coverage By Tag")
        lines.extend(self._format_counter(tag_counts))

        lines.append("")
        lines.append("Validated Check Types")
        lines.extend(self._format_counter(check_counts))

        if failed_check_counts:
            lines.append("")
            lines.append("Failed Check Types")
            lines.extend(self._format_counter(failed_check_counts))

        lines.append("")
        lines.append("Observability Coverage")
        lines.append(f"  Cases with traces   : {traced_cases}/{summary.total_cases}")
        lines.append(f"  Total traced nodes  : {total_trace_nodes}")
        lines.append(f"  Tool metric records : {tool_metric_count}")
        lines.append(f"  LLM metric records  : {llm_metric_count}")

        lines.append("")
        lines.append("Latency Breakdown")
        if results:
            fastest = min(results, key=lambda result: result.latency_ms)
            slowest = max(results, key=lambda result: result.latency_ms)
            lines.append(
                f"  Fastest case        : {fastest.case_id} ({fastest.latency_ms:.2f} ms)"
            )
            lines.append(
                f"  Slowest case        : {slowest.case_id} ({slowest.latency_ms:.2f} ms)"
            )
            lines.append(f"  Average latency     : {summary.average_latency_ms:.2f} ms")
        else:
            lines.append("  No cases executed.")

        return lines

    def _format_counter(
        self,
        counter: Counter[str],
    ) -> list[str]:
        if not counter:
            return ["  none: 0"]

        return [f"  {key}: {count}" for key, count in sorted(counter.items())]

    def _observed_value(
        self,
        *,
        observed: dict[str, Any] | None,
        key: str,
        expected_value: Any,
    ) -> Any:
        if observed is None:
            return None

        if key == "agent_name":
            routing_decision = observed.get("routing_decision") or {}
            return routing_decision.get("agent_name")

        if key == "tool_name":
            return observed.get("tool_used")

        if key == "ticket_created":
            return bool(observed.get("ticket_id"))

        if key == "escalated":
            metrics = self._trace_metrics(observed)
            return metrics.get("escalated")

        if key == "arguments":
            extracted = observed.get("extracted_arguments") or {}
            return extracted.get("values", {})

        if key == "response_contains":
            response = observed.get("response") or ""
            return {term: term.lower() in response.lower() for term in expected_value}

        return observed.get(key)

    def _observed_summary(
        self,
        observed: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if observed is None:
            return {}

        routing_decision = observed.get("routing_decision") or {}
        tool_decision = observed.get("tool_decision") or {}
        extracted = observed.get("extracted_arguments") or {}
        trace = observed.get("execution_trace") or {}
        escalation = observed.get("escalation_response") or {}

        tool_metrics = trace.get("tool_metrics") or []
        llm_metrics = trace.get("llm_metrics") or []
        nodes = trace.get("nodes") or []

        return {
            "agent": routing_decision.get("agent_name"),
            "tool_decision": tool_decision.get("tool_name"),
            "tool_used": observed.get("tool_used"),
            "arguments": extracted.get("values", {}),
            "missing_arguments": observed.get("missing_arguments", []),
            "needs_clarification": observed.get("needs_clarification"),
            "needs_human": observed.get("needs_human"),
            "ticket_id": observed.get("ticket_id"),
            "escalation_id": escalation.get("escalation_id"),
            "response": observed.get("response"),
            "trace_nodes": len(nodes),
            "tool_metrics": [metric.get("tool_name") for metric in tool_metrics],
            "llm_metrics_count": len(llm_metrics),
        }

    def _trace_metrics(
        self,
        observed: dict[str, Any],
    ) -> dict[str, Any]:
        trace = observed.get("execution_trace") or {}
        return trace.get("metrics") or {}

    def _console_safe(self, text: str) -> str:
        return text.replace("\u09f3", "BDT ")
