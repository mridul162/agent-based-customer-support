"""
Validate the evaluation workflow for the complete multi-agent architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.pipelines.multiagent_workflow_evaluation import run_evaluation


def main() -> None:
    report = run_evaluation()
    print(report)

    if "Failed            : 0" not in report:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
