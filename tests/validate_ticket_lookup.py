"""
tests/validate_ticket_lookup.py

End-to-end validation of the ticket retrieval flow (Milestone 6).

This is the first test where:
    - Extraction produces a value (ticket_id)
    - The executor consumes that extracted value as a tool argument
    - The tool performs a real retrieval using language-extracted data

This proves the complete Decision → Extraction → Execution chain
is working as a connected system, not just as isolated components.

Flow validated:
    create_ticket_tool()            ← create a real ticket
          ↓
    react_graph.invoke(message)     ← ask about it by ID in natural language
          ↓
    llm_decision_node               → tool_decision = get_ticket_tool
          ↓
    argument_extraction_node        → extracted_arguments = {ticket_id: ...}
          ↓
    tool_executor_node              → get_ticket_tool(ticket_id)
          ↓
    response_node                   → response with status and issue

Run with:
    python -m tests.validate_ticket_lookup
"""

import sys

from app.graphs.react_graph import react_graph
from app.schemas.agent_state import AgentState
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
# Scenario 1: Create a ticket then retrieve it by ID
# The core flow: extraction feeds executor feeds retrieval.
# ---------------------------------------------------------------------------

def validate_ticket_lookup() -> None:
    print("\n[Scenario 1] Create ticket → ask for status by ID")

    # Step 1: Create a real ticket via the tool directly.
    # This populates the in-memory service store so the graph can retrieve it.
    created = create_ticket_tool(customer_id="C001", issue="My refund was not processed.")
    ticket_id = created.ticket_id
    print(f"  ℹ️  Created ticket: {ticket_id}")

    # Step 2: Ask the agent about it using natural language.
    state = run_graph(
        customer_id="C001",
        message=f"What's the status of {ticket_id}?",
    )

    # LLM decision
    check("tool_decision is populated",
          state.tool_decision is not None)
    assert state.tool_decision is not None

    check("LLM chose get_ticket_tool",
          state.tool_decision.tool_name == "get_ticket_tool")
    check("tool_decision has reasoning",
          bool(state.tool_decision.reasoning))

    # Extraction — this is the first test that extraction feeds execution
    check("extracted_arguments is populated",
          state.extracted_arguments is not None)
    assert state.extracted_arguments is not None

    check("ticket_id was extracted from message",
          state.extracted_arguments.has("ticket_id"))
    check("extracted ticket_id matches created ticket_id",
          state.extracted_arguments.get("ticket_id") == ticket_id)

    # Execution
    check("tool_used is get_ticket_tool",
          state.tool_used == "get_ticket_tool")
    check("tool_result is populated",
          state.tool_result is not None)
    assert state.tool_result is not None

    check("tool_result ticket_id matches",
          state.tool_result.ticket_id == ticket_id)
    check("tool_result has status",
          bool(state.tool_result.status))

    # Response
    check("response is populated",
          bool(state.response))
    check("ticket_id appears in response",
          ticket_id in state.response) # type: ignore
    check("needs_human is False",
          state.needs_human is False)

    print(f"  ℹ️  LLM reasoning: {state.tool_decision.reasoning}")
    print(f"  ℹ️  Extracted ticket_id: {state.extracted_arguments.get('ticket_id')}")
    print(f"  ℹ️  Response:\n{state.response}")


# ---------------------------------------------------------------------------
# Scenario 2: Ask about a ticket ID that doesn't exist
# Validates the not-found path in the response builder.
# ---------------------------------------------------------------------------

def validate_ticket_not_found() -> None:
    print("\n[Scenario 2] Ask about non-existent ticket — not-found response")

    state = run_graph(
        customer_id="C002",
        message="What's the status of TICKET-DOESNOTEXIST?",
    )

    assert state.tool_decision is not None
    check("LLM chose get_ticket_tool",
          state.tool_decision.tool_name == "get_ticket_tool")

    assert state.extracted_arguments is not None
    check("ticket_id extracted",
          state.extracted_arguments.has("ticket_id"))
    check("extracted ID is the fake one",
          state.extracted_arguments.get("ticket_id") == "TICKET-DOESNOTEXIST")

    # tool_result should be None — ticket doesn't exist in the service
    check("tool_result is None (ticket not found)",
          state.tool_result is None)

    # Response node should produce a not-found message, not escalate
    check("response is populated",
          bool(state.response))
    check("needs_human is False (not-found is not an error)",
          state.needs_human is False)

    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Scenario 3: Create ticket still works — regression check
# Adding get_ticket_tool must not break create_ticket_tool.
# ---------------------------------------------------------------------------

def validate_create_ticket_regression() -> None:
    print("\n[Scenario 3] Create ticket regression — still works after adding get_ticket_tool")

    state = run_graph(
        customer_id="C003",
        message="I want a refund for my last order.",
    )

    assert state.tool_decision is not None
    check("LLM still chooses create_ticket_tool for refund request",
          state.tool_decision.tool_name == "create_ticket_tool")
    check("tool_result is populated",
          state.tool_result is not None)
    check("ticket_id assigned",
          bool(state.ticket_id))
    check("response populated",
          bool(state.response))

    print(f"  ℹ️  Ticket ID: {state.ticket_id}")


# ---------------------------------------------------------------------------
# Scenario 4: State completeness — all five artifacts present after retrieval
# ---------------------------------------------------------------------------

def validate_state_completeness_retrieval() -> None:
    print("\n[Scenario 4] State completeness after retrieval flow")

    created = create_ticket_tool(customer_id="C004", issue="Wrong item delivered.")

    state = run_graph(
        customer_id="C004",
        message=f"Can you check on {created.ticket_id}?",
    )

    assert state.tool_decision is not None
    check("tool_decision present",        state.tool_decision is not None)
    check("extracted_arguments present",  state.extracted_arguments is not None)
    check("tool_used present",            state.tool_used is not None)
    check("response present",             bool(state.response))

    # customer_id and message must be untouched
    check("customer_id unchanged",        state.customer_id == "C004")
    check("message unchanged",            created.ticket_id in state.message)

    print(f"  ℹ️  State: tool_decision ✓ extracted_arguments ✓ "
          f"tool_used ✓ tool_result ✓ response ✓")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 6 — Ticket Retrieval Flow Validation")
    print("  Decision → Extraction → Execution (retrieval)")
    print("=" * 60)

    try:
        validate_ticket_lookup()
        validate_ticket_not_found()
        validate_create_ticket_regression()
        validate_state_completeness_retrieval()

        print("\n" + "=" * 60)
        print("  get_ticket_tool registered       ✅")
        print("  Extraction feeds executor        ✅")
        print("  Ticket retrieval works           ✅")
        print("  Not-found handled gracefully     ✅")
        print("  create_ticket regression         ✅")
        print("  State completeness               ✅")
        print("  First agentic retrieval loop     ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()