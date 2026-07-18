"""
tests/validate_argument_validation.py

Validation of Milestone 7 — Argument Validation and Clarification Flow.

Tests both the validation node in isolation and the full graph behavior
when required arguments are missing from natural language input.

Key contract being validated:
    When required arguments are missing after extraction:
        state.needs_clarification = True
        state.missing_arguments   = [list of missing fields]
        execution is skipped
        response is a targeted clarification prompt

    When required arguments are present:
        state.needs_clarification = False
        state.missing_arguments   = []
        execution proceeds normally

Run with:
    python -m tests.validate_argument_validation
"""

import sys

from app.graphs.react_graph import react_graph
from app.nodes.argument_validation_node import argument_validation_node
from app.schemas.agent_state import AgentState
from app.schemas.extracted_arguments import ExtractedArguments
from app.schemas.tool_decision import ToolDecision
from app.tools.ticket_tools import create_ticket_tool

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


def run_graph(customer_id: str, message: str) -> AgentState:
    result = react_graph.invoke({"customer_id": customer_id, "message": message})
    return AgentState(**result)


# ---------------------------------------------------------------------------
# Unit: validation node in isolation — missing ticket_id
# ---------------------------------------------------------------------------

def validate_unit_missing_ticket_id() -> None:
    print("\n[Unit 1] Validation node — get_ticket_tool with no ticket_id extracted")

    state = AgentState(
        customer_id="TEST",
        message="What's the status of my ticket?",
        tool_decision=ToolDecision(
            tool_name="get_ticket_tool",
            reasoning="Customer asked about ticket status.",
        ),
        extracted_arguments=ExtractedArguments(values={}),  # nothing extracted
    )
    state = argument_validation_node(state)

    check("needs_clarification is True",
          state.needs_clarification is True)
    check("missing_arguments contains ticket_id",
          "ticket_id" in state.missing_arguments)
    check("tool_result not touched",
          state.tool_result is None)
    check("response not touched",
          state.response is None)


# ---------------------------------------------------------------------------
# Unit: validation node in isolation — ticket_id present
# ---------------------------------------------------------------------------

def validate_unit_ticket_id_present() -> None:
    print("\n[Unit 2] Validation node — get_ticket_tool with ticket_id extracted")

    state = AgentState(
        customer_id="TEST",
        message="What's the status of TICKET-123?",
        tool_decision=ToolDecision(
            tool_name="get_ticket_tool",
            reasoning="Customer referenced a ticket ID.",
        ),
        extracted_arguments=ExtractedArguments(values={"ticket_id": "TICKET-123"}),
    )
    state = argument_validation_node(state)

    check("needs_clarification is False",
          state.needs_clarification is False)
    check("missing_arguments is empty",
          state.missing_arguments == [])


# ---------------------------------------------------------------------------
# Unit: validation node — create_ticket_tool has no extraction requirements
# ---------------------------------------------------------------------------

def validate_unit_create_ticket_no_requirements() -> None:
    print("\n[Unit 3] Validation node — create_ticket_tool always passes validation")

    state = AgentState(
        customer_id="TEST",
        message="I need a refund.",
        tool_decision=ToolDecision(
            tool_name="create_ticket_tool",
            reasoning="Customer needs support.",
        ),
        extracted_arguments=ExtractedArguments(values={}),  # nothing needed
    )
    state = argument_validation_node(state)

    check("needs_clarification is False (no extraction required)",
          state.needs_clarification is False)
    check("missing_arguments is empty",
          state.missing_arguments == [])


# ---------------------------------------------------------------------------
# Unit: validation node — no_tool skips validation entirely
# ---------------------------------------------------------------------------

def validate_unit_no_tool_skips_validation() -> None:
    print("\n[Unit 4] Validation node — no_tool skips validation")

    state = AgentState(
        customer_id="TEST",
        message="Hello",
        tool_decision=ToolDecision(
            tool_name="no_tool",
            reasoning="Greeting only.",
        ),
    )
    state = argument_validation_node(state)

    check("needs_clarification remains False",
          state.needs_clarification is False)
    check("missing_arguments remains empty",
          state.missing_arguments == [])


# ---------------------------------------------------------------------------
# Integration: full graph — ambiguous ticket request (no ID in message)
# Validates: execution skipped, clarification response produced
# ---------------------------------------------------------------------------

def validate_graph_missing_ticket_id() -> None:
    print("\n[Integration 1] Graph — 'What is the status of my ticket?' (no ID)")

    state = run_graph(
        customer_id="C001",
        message="What is the status of my ticket?",
    )

    assert state.tool_decision is not None
    check("LLM chose get_ticket_tool",
          state.tool_decision.tool_name == "get_ticket_tool")

    check("needs_clarification is True",
          state.needs_clarification is True)
    check("ticket_id in missing_arguments",
          "ticket_id" in state.missing_arguments)
    check("execution was skipped (tool_used is None)",
          state.tool_used is None)
    check("tool_result is None (execution skipped)",
          state.tool_result is None)
    check("response is a clarification prompt",
          bool(state.response))
    check("response mentions ticket ID",
          "ticket" in state.response.lower()) # type: ignore
    check("needs_human is False (missing arg is not a system error)",
          state.needs_human is False)

    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Integration: full graph — ticket request WITH ID (regression: still works)
# ---------------------------------------------------------------------------

def validate_graph_with_ticket_id() -> None:
    print("\n[Integration 2] Graph — ticket request with ID (validation passes)")

    created = create_ticket_tool(customer_id="C002", issue="Damaged product received.")
    ticket_id = created.ticket_id

    state = run_graph(
        customer_id="C002",
        message=f"What's the status of {ticket_id}?",
    )

    assert state.tool_decision is not None
    check("LLM chose get_ticket_tool",
          state.tool_decision.tool_name == "get_ticket_tool")
    check("needs_clarification is False",
          state.needs_clarification is False)
    check("missing_arguments is empty",
          state.missing_arguments == [])
    check("execution ran (tool_used populated)",
          state.tool_used == "get_ticket_tool")
    check("tool_result is populated",
          state.tool_result is not None)
    check("response contains ticket ID",
          ticket_id in state.response) # type: ignore

    print(f"  ℹ️  Ticket ID: {ticket_id}")
    print(f"  ℹ️  Response:\n{state.response}")


# ---------------------------------------------------------------------------
# Integration: create_ticket regression — validation must not block it
# ---------------------------------------------------------------------------

def validate_graph_create_ticket_regression() -> None:
    print("\n[Integration 3] Graph — create_ticket regression after validation added")

    state = run_graph(
        customer_id="C003",
        message="I want a refund for my damaged order.",
    )

    assert state.tool_decision is not None
    check("LLM chose create_ticket_tool",
          state.tool_decision.tool_name == "create_ticket_tool")
    check("needs_clarification is False",
          state.needs_clarification is False)
    check("execution ran (tool_used populated)",
          state.tool_used == "create_ticket_tool")
    check("ticket created",
          bool(state.ticket_id))
    check("response populated",
          bool(state.response))

    print(f"  ℹ️  Ticket ID: {state.ticket_id}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 7 — Argument Validation & Clarification")
    print("=" * 60)

    try:
        validate_unit_missing_ticket_id()
        validate_unit_ticket_id_present()
        validate_unit_create_ticket_no_requirements()
        validate_unit_no_tool_skips_validation()
        validate_graph_missing_ticket_id()
        validate_graph_with_ticket_id()
        validate_graph_create_ticket_regression()

        print("\n" + "=" * 60)
        print("  Validation node (unit)         ✅")
        print("  Missing args → clarification   ✅")
        print("  Present args → execution       ✅")
        print("  Execution skipped on missing   ✅")
        print("  Tools assume valid args        ✅")
        print("  create_ticket regression       ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()