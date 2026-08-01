"""
Backward-compatible validation entrypoint.

The project no longer evaluates the old SupportAgent. This script now runs
the complete multi-agent workflow evaluation through router_graph.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.pipelines.multiagent_workflow_evaluation import main


if __name__ == "__main__":
    main()
