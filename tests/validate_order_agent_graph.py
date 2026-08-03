"""
tests/validate_order_agent_graph.py

Purpose:
--------
Validate the order specialist agent graph.

This script verifies:
- order_agent_graph selects the correct order tool.
- order_id and new_address extraction works.
- shared validation prompts for missing order IDs.
- tool execution and response building work through TOOL_REGISTRY.
- Tool metrics and node traces are recorded.
- agent_dispatch_node can invoke order_agent from AGENT_REGISTRY.

run:
    python -m tests.validate_order_agent_graph
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.agent_registry import AGENT_REGISTRY
from app.graphs.order_agent import order_agent_graph
from app.nodes.agent_dispatch_node import agent_dispatch_node
from app.schemas.agent_state import AgentState
from app.schemas.execution_trace import ExecutionTrace
from app.schemas.routing_decision import RoutingDecision
from app.schemas.tool_decision import ToolDecision
from app.schemas.tool_spec import ToolSpec
from app.tools import tool_registry

PASS = "PASS"
FAIL = "FAIL"


def check(condition: bool, message: str) -> None:
    status = PASS if condition else FAIL
    symbol = "[OK]" if condition else "[FAIL]"
    print(f"  {symbol} {status:<6} {message}")

    if not condition:
        raise AssertionError(message)


class FakeOrder:
    def __init__(
        self,
        *,
        order_id: str = "ORD-1001",
        status: str = "processing",
        delivery_address: str = "Dhaka",
    ):
        self.order_id = order_id
        self.status = type("Status", (), {"value": status})()
        self.customer_id = "customer-order-validation"
        self.total_amount = 1200.0
        self.delivery_address = delivery_address
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


def fake_get_order_status_tool(order_id: str):
    if order_id != "ORD-1001":
        return None
    return FakeOrder()


def fake_cancel_order_tool(order_id: str):
    if order_id != "ORD-1001":
        return None
    return FakeOrder(status="cancelled")


def fake_update_delivery_address_tool(order_id: str, new_address: str):
    if order_id != "ORD-1001":
        return None
    return FakeOrder(delivery_address=new_address)


def fake_estimate_delivery_time_tool(order_id: str):
    if order_id != "ORD-1001":
        return None
    return "Your order is being prepared for shipment."


def fake_order_parse_chat_completion(**kwargs):
    message = kwargs["messages"][-1]["content"].lower()

    if any(word in message for word in ("cancel", "cancellation")):
        tool_name = "cancel_order_tool"
        reasoning = "Customer wants to cancel an order."

    elif "address" in message and any(
        word in message for word in ("update", "change", "deliver", "ship")
    ):
        tool_name = "update_delivery_address_tool"
        reasoning = "Customer wants to update a delivery address."

    elif any(
        phrase in message
        for phrase in (
            "delivery time",
            "estimated delivery",
            "eta",
            "when will",
            "when does",
            "arrive",
            "delivered",
        )
    ):
        tool_name = "estimate_delivery_time_tool"
        reasoning = "Customer wants a delivery estimate."

    else:
        tool_name = "get_order_status_tool"
        reasoning = "Customer wants order status."

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=ToolDecision(
                        tool_name=tool_name,
                        reasoning=reasoning,
                    )
                )
            )
        ]
    )


@contextmanager
def patched_order_tools():
    original = tool_registry.TOOL_REGISTRY.copy()

    tool_registry.TOOL_REGISTRY.update(
        {
            "get_order_status_tool": ToolSpec(
                name="get_order_status_tool",
                tool_fn=fake_get_order_status_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_get_order_status_arguments,
                response_builder=tool_registry._build_get_order_status_response,
            ),
            "cancel_order_tool": ToolSpec(
                name="cancel_order_tool",
                tool_fn=fake_cancel_order_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_cancel_order_arguments,
                response_builder=tool_registry._build_cancel_order_response,
            ),
            "update_delivery_address_tool": ToolSpec(
                name="update_delivery_address_tool",
                tool_fn=fake_update_delivery_address_tool,
                required_arguments=("order_id", "new_address"),
                argument_builder=tool_registry._build_update_delivery_address_arguments,
                response_builder=tool_registry._build_update_delivery_address_response,
            ),
            "estimate_delivery_time_tool": ToolSpec(
                name="estimate_delivery_time_tool",
                tool_fn=fake_estimate_delivery_time_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_estimate_delivery_time_arguments,
                response_builder=tool_registry._build_estimate_delivery_time_response,
            ),
        }
    )

    with patch(
        "app.nodes.order_tool_decision_node.LLMService.parse_chat_completion",
        side_effect=fake_order_parse_chat_completion,
    ):
        try:
            yield
        finally:
            tool_registry.TOOL_REGISTRY.clear()
            tool_registry.TOOL_REGISTRY.update(original)


def build_state(message: str) -> AgentState:
    request_id = str(uuid4())

    return AgentState(
        request_id=request_id,
        customer_id="customer-order-validation",
        message=message,
        execution_trace=ExecutionTrace(
            request_id=request_id,
            customer_id="customer-order-validation",
            started_at=datetime.now(UTC),
        ),
    )


def invoke_order_agent(message: str) -> AgentState:
    state = build_state(message)
    result = order_agent_graph.invoke(state.model_dump())
    return AgentState(**result)


def validate_status_lookup() -> None:
    print("[1] Order status")

    with patched_order_tools():
        state = invoke_order_agent("What is the status of order ORD-1001?")

    check(state.tool_used == "get_order_status_tool", "Status tool selected")
    check(state.response is not None, "Response populated")
    check("ORD-1001" in state.response, "Response includes order ID")  # type: ignore
    check("processing" in state.response, "Response includes order status")  # type: ignore
    check(state.execution_trace is not None, "ExecutionTrace preserved")

    if state.execution_trace is not None:
        check(len(state.execution_trace.tool_metrics) == 1, "Tool metrics recorded")
        check(
            any(
                node.node_name == "order_tool_decision_node"
                for node in state.execution_trace.nodes
            ),
            "Order tool decision node traced",
        )


def validate_cancel_order() -> None:
    print("[2] Cancel order")

    with patched_order_tools():
        state = invoke_order_agent("Please cancel order ORD-1001")

    check(state.tool_used == "cancel_order_tool", "Cancel tool selected")
    check(state.response is not None, "Response populated")
    check("cancelled" in state.response.lower(), "Cancellation confirmed")  # type: ignore


def validate_update_address() -> None:
    print("[3] Update delivery address")

    with patched_order_tools():
        state = invoke_order_agent("Change address for ORD-1001 to Khulna Sadar")

    check(
        state.tool_used == "update_delivery_address_tool",
        "Update address tool selected",
    )
    check(state.response is not None, "Response populated")
    check("Khulna Sadar" in state.response, "New address included")  # type: ignore


def validate_delivery_estimate() -> None:
    print("[4] Delivery estimate")

    with patched_order_tools():
        state = invoke_order_agent("When will order ORD-1001 arrive?")

    check(
        state.tool_used == "estimate_delivery_time_tool",
        "Delivery estimate tool selected",
    )
    check(state.response is not None, "Response populated")
    check("shipment" in state.response.lower(), "Estimate response returned")  # type: ignore


def validate_missing_order_id() -> None:
    print("[5] Missing order ID")

    with patched_order_tools():
        state = invoke_order_agent("Track my order")

    check(state.needs_clarification, "Clarification requested")
    check("order_id" in state.missing_arguments, "order_id marked missing")
    check(state.tool_used is None, "Tool execution skipped")
    check(state.response is not None, "Clarification response populated")


def validate_registry_dispatch() -> None:
    print("[6] Registry dispatch")

    check("order_agent" in AGENT_REGISTRY, "order_agent registered")

    state = build_state("What is the status of order ORD-1001?")
    state.routing_decision = RoutingDecision(
        agent_name="order_agent",
        reasoning="Customer asked for order status.",
    )

    with patched_order_tools():
        result_state = agent_dispatch_node(state)

    check(result_state.response is not None, "Dispatch returns order response")
    check(
        result_state.tool_used == "get_order_status_tool",
        "Dispatch invokes order graph",
    )
    check(
        result_state.routing_decision is not None
        and result_state.routing_decision.agent_name == "order_agent",
        "Routing decision preserved",
    )


def main() -> None:
    print("=" * 64)
    print("  Order Agent Graph Validation")
    print("=" * 64)
    print()

    validate_status_lookup()
    print()

    validate_cancel_order()
    print()

    validate_update_address()
    print()

    validate_delivery_estimate()
    print()

    validate_missing_order_id()
    print()

    validate_registry_dispatch()
    print()

    print("=" * 64)
    print("  Order Agent Graph Validation Completed")
    print("=" * 64)


if __name__ == "__main__":
    main()
