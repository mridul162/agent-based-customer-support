"""
Executors used by the evaluation framework.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState
from app.schemas.escalation import (
    EscalationQueue,
    EscalationResponse,
    EscalationStatus,
)
from app.schemas.routing_decision import RoutingDecision
from app.schemas.ticket import TicketResponse, TicketStatus
from app.schemas.tool_decision import ToolDecision
from app.schemas.tool_spec import ToolSpec
from app.tools import tool_registry
from evaluation.interfaces.conversation_executor import ConversationExecutor


class RouterGraphExecutor(ConversationExecutor):
    """
    Execute the real multi-agent router graph.

    Set offline=True for deterministic evaluation against dummy datasets. The
    graph still runs end-to-end, but LLMs, DB-backed tools, memory, escalation,
    and RAG are replaced by deterministic fakes.
    """

    def __init__(self, *, offline: bool = True):
        self.offline = offline

    def execute(
        self,
        *,
        customer_id: str,
        message: str,
    ) -> AgentState:
        graph_input = {
            "customer_id": customer_id,
            "message": message,
            "request_id": f"EVAL-{uuid4()}",
        }

        if not self.offline:
            result = router_graph.invoke(graph_input)
            return AgentState(**result)

        with offline_multiagent_dependencies():
            result = router_graph.invoke(graph_input)
            return AgentState(**result)


class FakeRouterClient:
    @property
    def beta(self):
        return SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(parse=self._parse))
        )

    def _parse(self, **kwargs):
        message = kwargs["messages"][-1]["content"]
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(parsed=_route_for_message(message))
                )
            ]
        )


def _route_for_message(message: str) -> RoutingDecision:
    lowered = message.lower()

    if any(token in lowered for token in ("order", "ord-", "cancel", "address")):
        agent_name = "order_agent"
        reasoning = "Order management request."
    elif any(
        token in lowered
        for token in ("policy", "shipping", "warranty", "faq", "return")
    ):
        agent_name = "faq_agent"
        reasoning = "Knowledge-base question."
    else:
        agent_name = "ticket_agent"
        reasoning = "Support issue requiring ticket handling."

    return RoutingDecision(agent_name=agent_name, reasoning=reasoning)


def _tool_decision_for_message(**kwargs):
    message = kwargs["messages"][-1]["content"].lower()
    system_prompt = kwargs["messages"][0]["content"].lower()

    if "order management specialist" in system_prompt:
        if any(word in message for word in ("cancel", "cancellation")):
            tool_name = "cancel_order_tool"
        elif "address" in message and any(
            word in message for word in ("change", "update", "deliver", "ship")
        ):
            tool_name = "update_delivery_address_tool"
        elif any(
            word in message for word in ("arrive", "eta", "delivery time", "when will")
        ):
            tool_name = "estimate_delivery_time_tool"
        else:
            tool_name = "get_order_status_tool"
    else:
        if "ticket" in message and "status" in message:
            tool_name = "get_ticket_tool"
        elif any(
            word in message
            for word in (
                "refund",
                "damaged",
                "charged",
                "billing",
                "complaint",
                "never arrived",
            )
        ):
            tool_name = "create_ticket_tool"
        else:
            tool_name = "no_tool"

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    parsed=ToolDecision(
                        tool_name=tool_name,
                        reasoning=f"Offline evaluation selected {tool_name}.",
                    )
                )
            )
        ]
    )


def _fake_create_ticket_tool(customer_id: str, issue: str) -> TicketResponse:
    return TicketResponse(
        ticket_id=f"TICKET-{abs(hash((customer_id, issue))) % 100000}",
        customer_id=customer_id,
        issue=issue,
        status=TicketStatus.OPEN,
    )


def _fake_get_ticket_tool(ticket_id: str) -> TicketResponse | None:
    if not ticket_id:
        return None
    return TicketResponse(
        ticket_id=ticket_id,
        customer_id="evaluation-customer",
        issue="Existing support issue.",
        status=TicketStatus.OPEN,
    )


class FakeOrder:
    def __init__(
        self,
        *,
        order_id: str,
        status: str = "processing",
        delivery_address: str = "Dhaka",
    ):
        self.order_id = order_id
        self.customer_id = "evaluation-customer"
        self.status = SimpleNamespace(value=status)
        self.total_amount = 1200.0
        self.delivery_address = delivery_address
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


def _fake_get_order_status_tool(order_id: str):
    return FakeOrder(order_id=order_id)


def _fake_cancel_order_tool(order_id: str):
    return FakeOrder(order_id=order_id, status="cancelled")


def _fake_update_delivery_address_tool(order_id: str, new_address: str):
    return FakeOrder(order_id=order_id, delivery_address=new_address)


def _fake_estimate_delivery_time_tool(order_id: str):
    return "Your order is being prepared for shipment."


def _fake_retrieve_knowledge_tool(question: str, execution_trace=None) -> str:
    lowered = question.lower()
    if "shipping" in lowered:
        return "Standard shipping usually takes 3-5 business days."
    if "warranty" in lowered:
        return "Warranty coverage is based on the product warranty policy."
    return "I couldn't find that information in the knowledge base."


def _fake_create_escalation_tool(
    customer_id: str,
    reason: str,
    queue: str = "general",
) -> EscalationResponse:
    return EscalationResponse(
        escalation_id=f"ESC-{abs(hash((customer_id, reason, queue))) % 100000}",
        customer_id=customer_id,
        reason=reason,
        queue=EscalationQueue(queue),
        status=EscalationStatus.OPEN,
        created_at=datetime.now(UTC),
    )


@contextmanager
def offline_multiagent_dependencies():
    original_registry = tool_registry.TOOL_REGISTRY.copy()

    tool_registry.TOOL_REGISTRY.update(
        {
            "create_ticket_tool": ToolSpec(
                name="create_ticket_tool",
                tool_fn=_fake_create_ticket_tool,
                required_arguments=(),
                argument_builder=tool_registry._build_create_ticket_arguments,
                response_builder=tool_registry._build_create_ticket_response,
            ),
            "get_ticket_tool": ToolSpec(
                name="get_ticket_tool",
                tool_fn=_fake_get_ticket_tool,
                required_arguments=("ticket_id",),
                argument_builder=tool_registry._build_get_ticket_arguments,
                response_builder=tool_registry._build_get_ticket_response,
            ),
            "get_order_status_tool": ToolSpec(
                name="get_order_status_tool",
                tool_fn=_fake_get_order_status_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_get_order_status_arguments,
                response_builder=tool_registry._build_get_order_status_response,
            ),
            "cancel_order_tool": ToolSpec(
                name="cancel_order_tool",
                tool_fn=_fake_cancel_order_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_cancel_order_arguments,
                response_builder=tool_registry._build_cancel_order_response,
            ),
            "update_delivery_address_tool": ToolSpec(
                name="update_delivery_address_tool",
                tool_fn=_fake_update_delivery_address_tool,
                required_arguments=("order_id", "new_address"),
                argument_builder=tool_registry._build_update_delivery_address_arguments,
                response_builder=tool_registry._build_update_delivery_address_response,
            ),
            "estimate_delivery_time_tool": ToolSpec(
                name="estimate_delivery_time_tool",
                tool_fn=_fake_estimate_delivery_time_tool,
                required_arguments=("order_id",),
                argument_builder=tool_registry._build_estimate_delivery_time_arguments,
                response_builder=tool_registry._build_estimate_delivery_time_response,
            ),
        }
    )

    patches = [
        patch(
            "app.nodes.router_node.get_openai_client", return_value=FakeRouterClient()
        ),
        patch(
            "app.nodes.ticket_tool_decision_node.LLMService.parse_chat_completion",
            side_effect=_tool_decision_for_message,
        ),
        patch(
            "app.nodes.order_tool_decision_node.LLMService.parse_chat_completion",
            side_effect=_tool_decision_for_message,
        ),
        patch(
            "app.graphs.faq_agent.retrieve_knowledge_tool",
            side_effect=_fake_retrieve_knowledge_tool,
        ),
        patch(
            "app.graphs.escalation_agent.create_escalation_tool",
            side_effect=_fake_create_escalation_tool,
        ),
        patch(
            "app.nodes.memory_loader_node.conversation_service.get_history",
            return_value=[],
        ),
        patch(
            "app.nodes.memory_writer_node.conversation_service.append_turn",
            return_value=None,
        ),
        patch(
            "app.nodes.memory_writer_node.conversation_service.get_history",
            return_value=[],
        ),
    ]

    started = [p.start() for p in patches]
    try:
        yield started
    finally:
        for p in reversed(patches):
            p.stop()
        tool_registry.TOOL_REGISTRY.clear()
        tool_registry.TOOL_REGISTRY.update(original_registry)
