"""
tests/validate_argument_extraction.py

Isolated validation of the argument extraction subsystem.

Validates argument_extraction_node independently — no LLM, no tools,
no graph, no database. The node reads state.message and writes
state.extracted_arguments. That contract is all that's tested here.

This follows the same discipline used for:
    validate_ticket_tools.py    → Tool + Service layer
    validate_support_agent.py   → Agent layer
    validate_react_graph.py     → Full ReAct loop

Each subsystem validated in isolation before graph integration.

Run with:
    python -m tests.validate_argument_extraction
"""

import sys

from app.nodes.argument_extraction_node import argument_extraction_node
from app.schemas.agent_state import AgentState

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


def run_extraction(message: str) -> AgentState:
    """Run the extraction node against a message and return final state."""
    state = AgentState(customer_id="TEST", message=message)
    return argument_extraction_node(state)


# ---------------------------------------------------------------------------
# Case 1: Standard uppercase ticket ID
# ---------------------------------------------------------------------------

def validate_standard_ticket_id() -> None:
    print('\n[Case 1] Standard ticket ID — "TICKET-123"')

    state = run_extraction("What's the status of ticket TICKET-123?")

    check("extracted_arguments is populated",
          state.extracted_arguments is not None)
    assert state.extracted_arguments is not None

    check("ticket_id is found",
          state.extracted_arguments.has("ticket_id"))
    check("ticket_id value is correct",
          state.extracted_arguments.get("ticket_id") == "TICKET-123")
    check("no extra keys extracted",
          list(state.extracted_arguments.values.keys()) == ["ticket_id"])


# ---------------------------------------------------------------------------
# Case 2: Lowercase ticket ID — normalised to uppercase
# ---------------------------------------------------------------------------

def validate_lowercase_ticket_id() -> None:
    print('\n[Case 2] Lowercase ticket ID normalised — "ticket-abc123"')

    state = run_extraction("I have a question about ticket-abc123")

    assert state.extracted_arguments is not None
    check("ticket_id is found",
          state.extracted_arguments.has("ticket_id"))
    check("ticket_id normalised to uppercase",
          state.extracted_arguments.get("ticket_id") == "TICKET-ABC123")


# ---------------------------------------------------------------------------
# Case 3: Alphanumeric ticket ID (matches real generated IDs like TICKET-34D61027)
# ---------------------------------------------------------------------------

def validate_alphanumeric_ticket_id() -> None:
    print('\n[Case 3] Alphanumeric ticket ID — "TICKET-34D61027"')

    state = run_extraction("Can you update ticket TICKET-34D61027 for me?")

    assert state.extracted_arguments is not None
    check("ticket_id is found",
          state.extracted_arguments.has("ticket_id"))
    check("ticket_id value is correct",
          state.extracted_arguments.get("ticket_id") == "TICKET-34D61027")


# ---------------------------------------------------------------------------
# Case 4: No ticket ID in message — empty extraction is valid
# ---------------------------------------------------------------------------

def validate_no_ticket_id() -> None:
    print('\n[Case 4] No entity in message — "Hello"')

    state = run_extraction("Hello")

    assert state.extracted_arguments is not None
    check("extracted_arguments is populated (even when empty)",
          state.extracted_arguments is not None)
    check("no ticket_id found",
          not state.extracted_arguments.has("ticket_id"))
    check("values dict is empty",
          state.extracted_arguments.values == {})


# ---------------------------------------------------------------------------
# Case 5: Refund message with no ticket ID — extraction finds nothing
# ---------------------------------------------------------------------------

def validate_refund_no_ticket() -> None:
    print('\n[Case 5] Refund request without ticket ID — empty extraction')

    state = run_extraction("I want a refund for my last order.")

    assert state.extracted_arguments is not None
    check("no ticket_id extracted",
          not state.extracted_arguments.has("ticket_id"))
    check("values dict is empty",
          state.extracted_arguments.values == {})


# ---------------------------------------------------------------------------
# Case 6: Message independence from tool_decision
# The extraction node must not read state.tool_decision.
# Proof: run extraction on a message that would trigger no_tool,
# and confirm ticket_id is still extracted if present.
# ---------------------------------------------------------------------------

def validate_extraction_independent_of_tool_decision() -> None:
    print('\n[Case 6] Extraction independent of tool_decision')

    # tool_decision is deliberately left None — simulating a state
    # where the decision node hasn't run yet or chose no_tool.
    # Extraction must still work on the message alone.
    state = AgentState(
        customer_id="TEST",
        message="Just checking on TICKET-999 — no action needed.",
        tool_decision=None,
    )
    state = argument_extraction_node(state)

    assert state.extracted_arguments is not None
    check("ticket_id extracted even with no tool_decision",
          state.extracted_arguments.has("ticket_id"))
    check("ticket_id value correct",
          state.extracted_arguments.get("ticket_id") == "TICKET-999")
    check("tool_decision still None (extraction didn't touch it)",
          state.tool_decision is None)


# ---------------------------------------------------------------------------
# Case 7: Ticket ID mid-sentence, no surrounding whitespace boundary issues
# ---------------------------------------------------------------------------

def validate_ticket_id_mid_sentence() -> None:
    print('\n[Case 7] Ticket ID embedded in sentence')

    state = run_extraction("Please check TICKET-XYZ999 as soon as possible.")

    assert state.extracted_arguments is not None
    check("ticket_id found mid-sentence",
          state.extracted_arguments.has("ticket_id"))
    check("ticket_id value correct",
          state.extracted_arguments.get("ticket_id") == "TICKET-XYZ999")


# ---------------------------------------------------------------------------
# Case 8: get() convenience method returns default for missing keys
# ---------------------------------------------------------------------------

def validate_get_default() -> None:
    print('\n[Case 8] .get() returns default for missing entity')

    state = run_extraction("I need help with my account.")

    assert state.extracted_arguments is not None
    result = state.extracted_arguments.get("ticket_id", "NOT_FOUND")
    check(".get() returns default when key absent",
          result == "NOT_FOUND")

    result_none = state.extracted_arguments.get("order_id")
    check(".get() returns None by default when key absent",
          result_none is None)


# ---------------------------------------------------------------------------
# Case 9: State fields not written by extraction remain untouched
# ---------------------------------------------------------------------------

def validate_state_isolation() -> None:
    print('\n[Case 9] Extraction only writes extracted_arguments — other fields untouched')

    state = run_extraction("Check ticket TICKET-555 please.")

    check("customer_id unchanged",       state.customer_id == "TEST")
    check("message unchanged",           "TICKET-555" in state.message)
    check("tool_decision still None",    state.tool_decision is None)
    check("tool_result still None",      state.tool_result is None)
    check("tool_used still None",        state.tool_used is None)
    check("response still None",         state.response is None)
    check("needs_human still False",     state.needs_human is False)
    check("ticket_id on state still None",  state.ticket_id is None)


# ---------------------------------------------------------------------------
# Case 10: Multiple ticket IDs — first match wins (business decision)
# ---------------------------------------------------------------------------

def validate_first_match_wins() -> None:
    print('\n[Case 10] Multiple ticket IDs — first match wins')

    state = run_extraction("Check TICKET-111 and also TICKET-222 please.")

    assert state.extracted_arguments is not None
    check("ticket_id is found",
          state.extracted_arguments.has("ticket_id"))
    check("first ticket ID is returned (TICKET-111, not TICKET-222)",
          state.extracted_arguments.get("ticket_id") == "TICKET-111")
    check("only one ticket_id key present (no TICKET-222)",
          list(state.extracted_arguments.values.keys()) == ["ticket_id"])

    # Why first-match-wins?
    # When a customer mentions two ticket IDs, it's ambiguous which one
    # they mean. Silently choosing the second would be equally arbitrary.
    # First-match is deterministic, testable, and forces the ambiguity
    # to surface — future improvement: detect multiple IDs and ask for
    # clarification instead of silently dropping one.


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Argument Extraction Node — Isolated Validation")
    print("=" * 60)

    try:
        validate_standard_ticket_id()
        validate_lowercase_ticket_id()
        validate_alphanumeric_ticket_id()
        validate_no_ticket_id()
        validate_refund_no_ticket()
        validate_extraction_independent_of_tool_decision()
        validate_ticket_id_mid_sentence()
        validate_get_default()
        validate_state_isolation()
        validate_first_match_wins()

        print("\n" + "=" * 60)
        print("  Regex extraction (ticket_id)    ✅")
        print("  Uppercase normalisation         ✅")
        print("  Empty extraction (valid)        ✅")
        print("  tool_decision independence      ✅")
        print("  State isolation                 ✅")
        print("  ExtractedArguments API          ✅")
        print("  First-match-wins (multi-ID)    ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()