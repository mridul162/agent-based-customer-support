"""
app/tools/tool_registry.py

Purpose:
--------
Single source of truth for all registered tools.

Each tool is described by one ToolSpec instance that captures everything
needed to validate, execute, and respond for that tool.

Responsibilities:
-----------------
- Define argument builders (previously in tool_executor_node.py).
- Define response builders (previously in response_node.py).
- Construct ToolSpec instances for each tool.
- Expose TOOL_REGISTRY as the single dict nodes import from.

This module DOES NOT:
---------------------
- Execute tools at registration time.
- Read AgentState at import time (only at invocation time via builders).
- Own business logic — builders and tools own that.
- Know about LangGraph, nodes, or the graph structure.

Architecture payoff:
--------------------
Before Milestone 8, adding a new tool required edits in four files:
    tool_executor_node.py      (_TOOL_REGISTRY, _ARGUMENT_BUILDERS)
    argument_validation_node.py (_REQUIRED_ARGUMENTS)
    response_node.py            (_RESPONSE_BUILDERS)

After Milestone 8, adding a new tool requires editing one file:
    app/tools/tool_registry.py

Procedure for adding a new tool:
    1. Import the tool function.
    2. Define an argument builder function.
    3. Define a response builder function.
    4. Add one ToolSpec entry to TOOL_REGISTRY.
    Done. No other files change.
"""

from typing import Any

from app.schemas.agent_state import AgentState
from app.schemas.tool_spec import ToolSpec
from app.tools.order_tools import cancel_order_tool, estimate_delivery_time_tool, get_order_status_tool, update_delivery_address_tool
from app.tools.retrieve_knowledge_tool import retrieve_knowledge_tool
from app.tools.ticket_tools import create_ticket_tool, get_ticket_tool


# ---------------------------------------------------------------------------
# Argument Builders
#
# Each builder reads from AgentState and returns the kwargs dict
# passed to the corresponding tool function.
#
# Design B in practice: builders read from state fields or extracted_arguments.
# The LLM is not asked to re-state values that already exist in state.
# ---------------------------------------------------------------------------

def _build_create_ticket_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for create_ticket_tool.
    Both values always exist in AgentState — no extraction required.
    """
    return {
        "customer_id": state.customer_id,
        "issue":       state.message,
    }


def _build_get_ticket_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for get_ticket_tool.
    ticket_id is extracted from natural language by argument_extraction_node.
    Validation guarantees it is present before execution reaches here.
    """
    return {
        "ticket_id": (
            state.extracted_arguments.get("ticket_id")
            if state.extracted_arguments is not None
            else None
        ),
    }


def _build_retrieve_knowledge_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for retrieve_knowledge_tool.
    The customer's current message is the retrieval query.
    """
    return {
        "question": state.message,
        "execution_trace": state.execution_trace,
    }

def _build_get_order_status_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for get_order_status_tool.
    order_id is extracted from natural language by argument_extraction_node.
    Validation guarantees it is present before execution reaches here.
    """
    return {
        "order_id": (
            state.extracted_arguments.get("order_id")
            if state.extracted_arguments is not None
            else None
        ),
    }

def _build_cancel_order_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for cancel_order_tool.
    order_id is extracted from natural language by argument_extraction_node.
    Validation guarantees it is present before execution reaches here.
    """
    return {
        "order_id": (
            state.extracted_arguments.get("order_id")
            if state.extracted_arguments is not None
            else None
        ),
    }

def _build_update_delivery_address_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for update_delivery_address_tool.
    order_id and new_address are extracted from natural language by argument_extraction_node.
    Validation guarantees they are present before execution reaches here.
    """
    return {
        "order_id": (
            state.extracted_arguments.get("order_id")
            if state.extracted_arguments is not None
            else None
        ),
        "new_address": (
            state.extracted_arguments.get("new_address")
            if state.extracted_arguments is not None
            else None
        ),
    }

def _build_estimate_delivery_time_arguments(state: AgentState) -> dict[str, Any]:
    """
    Arguments for estimate_delivery_time_tool.
    order_id is extracted from natural language by argument_extraction_node.
    Validation guarantees it is present before execution reaches here.
    """
    return {
        "order_id": (
            state.extracted_arguments.get("order_id")
            if state.extracted_arguments is not None
            else None
        ),
    }


# ---------------------------------------------------------------------------
# Response Builders
#
# Each builder converts the raw tool result into a customer-facing string.
# Receives tool_result including None — each builder interprets None
# according to its tool's specific semantics.
# ---------------------------------------------------------------------------

def _build_create_ticket_response(tool_result: Any) -> str:
    """
    Confirmation message for a successfully created ticket.
    Returns empty string on None — signals escalation to response_node.
    """
    if tool_result is None:
        return ""   # Signals failure → response_node escalates
    return (
        f"Your support ticket has been created successfully.\n\n"
        f"Ticket ID: {tool_result.ticket_id}\n\n"
        f"Our team will review your request and contact you shortly."
    )


def _build_get_ticket_response(tool_result: Any) -> str:
    """
    Status response for a ticket lookup.
    None means ticket not found (user error) — return polite not-found message.
    This is NOT escalated because a missing ticket is recoverable by the user.
    """
    if tool_result is None:
        return (
            "We could not find a ticket with that ID. "
            "Please verify the ticket number and try again."
        )
    return (
        f"Here is the status of your ticket:\n\n"
        f"Ticket ID: {tool_result.ticket_id}\n"
        f"Status:    {tool_result.status.value}\n"
        f"Issue:     {tool_result.issue}"
    )


def _build_retrieve_knowledge_response(tool_result: Any) -> str:
    """
    RAG returns a customer-facing answer string.
    """
    if tool_result is None:
        return ""
    return str(tool_result).strip()

def _order_not_found_response() -> str:
    return (
        "We could not find an order with that ID. "
        "Please verify the order number and try again."
    )

def _build_get_order_status_response(tool_result: Any) -> str:
    """
    Returns a customer-facing order status string.
    """
    if tool_result is None:
        return _order_not_found_response()
    return (
        f"Here is the status of your order:\n\n"
        f"Order ID: {tool_result.order_id}\n"
        f"Status:   {tool_result.status.value}\n"
        f"Total:    ৳{tool_result.total_amount:.2f}\n"
        f"Address:  {tool_result.delivery_address}\n"
        f"Last Updated: {tool_result.updated_at:%Y-%m-%d %H:%M UTC}"
    )

def _build_cancel_order_response(tool_result: Any) -> str:
    """
    Returns a customer-facing order cancellation confirmation string.
    """
    if tool_result is None:
        return _order_not_found_response()
    return (
        f"Your order has been successfully cancelled.\n\n"
        f"Order ID: {tool_result.order_id}\n"
        f"Status:   {tool_result.status.value}"
    )

def _build_update_delivery_address_response(tool_result: Any) -> str:
    """
    Returns a customer-facing delivery address update confirmation string.
    """
    if tool_result is None:
        return _order_not_found_response()
    return (
        f"Your delivery address has been successfully updated.\n\n"
        f"Order ID: {tool_result.order_id}\n"
        f"New Address: {tool_result.delivery_address}"
    )

def _build_estimate_delivery_time_response(tool_result: Any) -> str:
    """
    Returns a customer-facing estimated delivery time string.
    """
    if tool_result is None:
        return _order_not_found_response()
    if isinstance(tool_result, str):
        return tool_result
    return (
        f"Your order is estimated to be delivered by {tool_result.estimated_delivery_time}."
    )


# ---------------------------------------------------------------------------
# Tool Registry
#
# The single source of truth for all tool registrations.
# Every node imports TOOL_REGISTRY and reads the ToolSpec it needs.
#
# Key: must match exactly what the LLM returns in ToolDecision.tool_name.
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, ToolSpec] = {
    "create_ticket_tool": ToolSpec(
        name               = "create_ticket_tool",
        tool_fn            = create_ticket_tool,
        required_arguments = (),           # customer_id + message always in state
        argument_builder   = _build_create_ticket_arguments,
        response_builder   = _build_create_ticket_response,
    ),

    "get_ticket_tool": ToolSpec(
        name               = "get_ticket_tool",
        tool_fn            = get_ticket_tool,
        required_arguments = ("ticket_id",), # must be extracted from language
        argument_builder   = _build_get_ticket_arguments,
        response_builder   = _build_get_ticket_response,
    ),

    "retrieve_knowledge_tool": ToolSpec(
        name               = "retrieve_knowledge_tool",
        tool_fn            = retrieve_knowledge_tool,
        required_arguments = (),
        argument_builder   = _build_retrieve_knowledge_arguments,
        response_builder   = _build_retrieve_knowledge_response,
    ),

    "get_order_status_tool": ToolSpec(
        name               = "get_order_status_tool",
        tool_fn            = get_order_status_tool,
        required_arguments = ("order_id",), # must be extracted from language
        argument_builder   = _build_get_order_status_arguments,
        response_builder   = _build_get_order_status_response,
    ),

    "cancel_order_tool": ToolSpec(
        name               = "cancel_order_tool",
        tool_fn            = cancel_order_tool,
        required_arguments = ("order_id",), # must be extracted from language
        argument_builder   = _build_cancel_order_arguments,
        response_builder   = _build_cancel_order_response,
    ),

    "update_delivery_address_tool": ToolSpec(
        name               = "update_delivery_address_tool",
        tool_fn            = update_delivery_address_tool,
        required_arguments = ("order_id", "new_address"), # must be extracted from language
        argument_builder   = _build_update_delivery_address_arguments,
        response_builder   = _build_update_delivery_address_response,
    ),

    "estimate_delivery_time_tool": ToolSpec(
        name               = "estimate_delivery_time_tool",
        tool_fn            = estimate_delivery_time_tool,
        required_arguments = ("order_id",), # must be extracted from language
        argument_builder   = _build_estimate_delivery_time_arguments,
        response_builder   = _build_estimate_delivery_time_response,
    ),
}
