from pathlib import Path

from app.agents.support_agent import SupportAgent

from evaluation.runners.tool_selection_runner import (
    ToolSelectionRunner,
)

from evaluation.interfaces.agent_executor import (
    SupportAgentExecutor,
)

from evaluation.evaluators.tool_selection_evaluator import (
    ToolSelectionEvaluator,
)

from evaluation.metrics import (
    EvaluationMetrics,
)

from evaluation.report_generator import (
    ReportGenerator,
)


def main() -> None:

    dataset = (
        Path(__file__).parent.parent
        / "datasets"
        / "tool_selection.json"
    )

    agent = SupportAgent()

    executor = SupportAgentExecutor(agent)

    runner = ToolSelectionRunner(
        dataset_path=str(dataset),
        executor=executor,
    )

    print("Running evaluation...")

    execution_results = runner.run()

    evaluator = ToolSelectionEvaluator()

    evaluation_results = evaluator.evaluate(
        execution_results
    )

    metrics = EvaluationMetrics()

    summary = metrics.compute(
        evaluation_results
    )

    report = ReportGenerator().generate(
        summary,
        title="Tool Selection Evaluation",
    )

    print(report)


if __name__ == "__main__":
    main()