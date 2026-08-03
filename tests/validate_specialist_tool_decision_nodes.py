"""
tests/validate_specialist_tool_decision_nodes.py

Validate the separate LLM decision nodes for ticket and order tools.

run:
    python -m tests.validate_specialist_tool_decision_nodes
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.nodes.order_tool_decision_node import order_tool_decision_node
from app.nodes.ticket_tool_decision_node import ticket_tool_decision_node
from app.prompts.order_tool_decision_prompt import (
    ORDER_TOOL_DECISION_SYSTEM_PROMPT,
)
from app.prompts.ticket_tool_decision_prompt import (
    TICKET_TOOL_DECISION_SYSTEM_PROMPT,
)
from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import ToolDecision

PASS = "PASS"
FAIL = "FAIL"


def check(condition: bool, message: str) -> None:
    status = PASS if condition else FAIL
    symbol = "[OK]" if condition else "[FAIL]"
    print(f"  {symbol} {status:<6} {message}")

    if not condition:
        raise AssertionError(message)


def completion(tool_name: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=ToolDecision(
                        tool_name=tool_name,
                        reasoning=f"Select {tool_name}.",
                    )
                )
            )
        ]
    )


def validate_ticket_decision_node() -> None:
    print("[1] Ticket tool decision node")

    calls = []

    def fake_parse_chat_completion(**kwargs):
        calls.append(kwargs)
        return completion("create_ticket_tool")

    state = AgentState(
        customer_id="customer-ticket-decision",
        message="I received a damaged product.",
    )

    with patch(
        "app.nodes.ticket_tool_decision_node.LLMService.parse_chat_completion",
        side_effect=fake_parse_chat_completion,
    ):
        state = ticket_tool_decision_node(state)

    check(state.tool_decision is not None, "Ticket decision populated")
    check(
        state.tool_decision is not None
        and state.tool_decision.tool_name == "create_ticket_tool",
        "Ticket node selects ticket tool",
    )
    check(
        calls[0]["messages"][0]["content"] == TICKET_TOOL_DECISION_SYSTEM_PROMPT,
        "Ticket node uses ticket prompt",
    )


def validate_order_decision_node() -> None:
    print("[2] Order tool decision node")

    calls = []

    def fake_parse_chat_completion(**kwargs):
        calls.append(kwargs)
        return completion("cancel_order_tool")

    state = AgentState(
        customer_id="customer-order-decision",
        message="Please cancel order ORD-1001.",
    )

    with patch(
        "app.nodes.order_tool_decision_node.LLMService.parse_chat_completion",
        side_effect=fake_parse_chat_completion,
    ):
        state = order_tool_decision_node(state)

    check(state.tool_decision is not None, "Order decision populated")
    check(
        state.tool_decision is not None
        and state.tool_decision.tool_name == "cancel_order_tool",
        "Order node selects order tool",
    )
    check(
        calls[0]["messages"][0]["content"] == ORDER_TOOL_DECISION_SYSTEM_PROMPT,
        "Order node uses order prompt",
    )


def main() -> None:
    print("=" * 64)
    print("  Specialist Tool Decision Node Validation")
    print("=" * 64)
    print()

    validate_ticket_decision_node()
    print()

    validate_order_decision_node()
    print()

    print("=" * 64)
    print("  Specialist Tool Decision Node Validation Completed")
    print("=" * 64)


if __name__ == "__main__":
    main()
