from pathlib import Path

from evaluation.evaluators.multiagent_workflow_evaluator import (
    MultiAgentWorkflowEvaluator,
)
from evaluation.interfaces.agent_executor import RouterGraphExecutor
from evaluation.metrics import EvaluationMetrics
from evaluation.report_generator import ReportGenerator
from evaluation.runners.multiagent_workflow_runner import (
    MultiAgentWorkflowRunner,
)


def run_evaluation() -> str:
    dataset = Path(__file__).parent.parent / "datasets" / "multiagent_workflow.json"

    runner = MultiAgentWorkflowRunner(
        dataset_path=str(dataset),
        executor=RouterGraphExecutor(offline=True),
    )

    execution_results = runner.run()
    evaluation_results = MultiAgentWorkflowEvaluator().evaluate(execution_results)
    summary = EvaluationMetrics().compute(evaluation_results)

    return ReportGenerator().generate(
        summary,
        title="Multi-Agent Workflow Evaluation",
    )


def main() -> None:
    print("Running multi-agent workflow evaluation...")
    print(run_evaluation())


if __name__ == "__main__":
    main()
