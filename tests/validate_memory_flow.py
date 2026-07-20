"""
tests/validate_memory_flow.py

End-to-end validation of Milestone 10 — Shared Memory & Conversation Context.

The key scenario:
    Turn 1: Customer reports a problem → ticket created.
    Turn 2: Customer asks "What's the status?" (no ticket ID in message).
    Memory:  Extraction recovers ticket_id from prior assistant response.
    Result:  Agent retrieves correct ticket without customer repeating ID.

This validates that isolated requests have become a genuine conversation.

Run with:
    python -m tests.validate_memory_flow
"""

import sys

from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState
from app.services.conversation_service import conversation_service

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


def run_router(customer_id: str, message: str) -> AgentState:
    result = router_graph.invoke({"customer_id": customer_id, "message": message})
    return AgentState(**result)


# ---------------------------------------------------------------------------
# Scenario 1: Full memory flow — create ticket, then ask status without ID
# The core scenario that justifies this entire milestone.
# ---------------------------------------------------------------------------

def validate_memory_retrieval_flow() -> None:
    print("\n[Scenario 1] Create ticket → ask status without ID → memory recovers")

    customer_id = "MEM-001"
    conversation_service.clear_history(customer_id)  # clean slate

    # Turn 1: create a ticket
    print("  ── Turn 1: reporting a delivery problem")
    state1 = run_router(
        customer_id=customer_id,
        message="My package never arrived.",
    )

    check("Turn 1: ticket was created",
          bool(state1.ticket_id))
    check("Turn 1: response mentions ticket ID",
          state1.ticket_id is not None and
          state1.response is not None and
          state1.ticket_id in state1.response)

    ticket_id = state1.ticket_id
    print(f"  ℹ️  Created ticket: {ticket_id}")
    print(f"  ℹ️  Response: {state1.response[:80]}...") # type: ignore

    # Verify Turn 1 was persisted to memory
    history_after_turn1 = conversation_service.get_history(customer_id)
    check("Turn 1: history has 2 messages (user + assistant)",
          len(history_after_turn1) == 2)
    check("Turn 1: first message is user role",
          history_after_turn1[0].role == "user")
    check("Turn 1: second message is assistant role",
          history_after_turn1[1].role == "assistant")
    check("Turn 1: ticket_id in persisted assistant message",
          ticket_id is not None and ticket_id in history_after_turn1[1].content)

    # Turn 2: ask for status WITHOUT providing the ticket ID
    print("\n  ── Turn 2: asking status (no ticket ID in message)")
    state2 = run_router(
        customer_id=customer_id,
        message="What's the status?",
    )

    check("Turn 2: history loaded (2 messages from Turn 1)",
          len(state2.conversation_history) == 2)
    check("Turn 2: ticket_id recovered from memory",
          state2.extracted_arguments is not None and
          state2.extracted_arguments.get("ticket_id") == ticket_id)
    check("Turn 2: get_ticket_tool was used",
          state2.tool_used == "get_ticket_tool")
    check("Turn 2: response populated",
          bool(state2.response))
    check("Turn 2: ticket_id appears in response",
          ticket_id is not None and
          state2.response is not None and
          ticket_id in state2.response)
    check("Turn 2: no clarification needed",
          state2.needs_clarification is False)

    print(f"  ℹ️  Memory recovered: {ticket_id}")
    print(f"  ℹ️  Response:\n{state2.response}")

    # Verify Turn 2 also persisted
    history_after_turn2 = conversation_service.get_history(customer_id)
    check("Turn 2: history now has 4 messages",
          len(history_after_turn2) == 4)


# ---------------------------------------------------------------------------
# Scenario 2: Fresh customer — no history, no memory fallback needed
# Validates that memory doesn't interfere with first-contact flows.
# ---------------------------------------------------------------------------

def validate_fresh_customer_no_memory() -> None:
    print("\n[Scenario 2] Fresh customer — no prior history")

    customer_id = "MEM-002"
    conversation_service.clear_history(customer_id)

    state = run_router(
        customer_id=customer_id,
        message="I want a refund for my damaged order.",
    )

    check("No history loaded for new customer",
          len(state.conversation_history) == 0)
    check("Ticket still created without memory",
          bool(state.ticket_id))
    check("Response populated",
          bool(state.response))

    # History should now have 2 messages
    history = conversation_service.get_history(customer_id)
    check("First interaction persisted to history",
          len(history) == 2)

    print(f"  ℹ️  Ticket: {state.ticket_id}")


# ---------------------------------------------------------------------------
# Scenario 3: History grows correctly across multiple turns
# ---------------------------------------------------------------------------

def validate_history_accumulation() -> None:
    print("\n[Scenario 3] History accumulates correctly across turns")

    customer_id = "MEM-003"
    conversation_service.clear_history(customer_id)

    run_router(customer_id=customer_id, message="My order arrived damaged.")
    run_router(customer_id=customer_id, message="I also want a refund.")

    history = conversation_service.get_history(customer_id)
    check("History has 4 messages after 2 turns",
          len(history) == 4)
    check("Messages alternate user/assistant/user/assistant",
          [m.role for m in history] == ["user", "assistant", "user", "assistant"])

    print(f"  ℹ️  History length: {len(history)} messages")


# ---------------------------------------------------------------------------
# Scenario 4: Ambiguous "What's the status?" with NO prior ticket
# Should still clarify (no ticket in history to recover from)
# ---------------------------------------------------------------------------

def validate_no_ticket_in_history() -> None:
    print("\n[Scenario 4] 'What's the status?' with no ticket in history")

    customer_id = "MEM-004"
    conversation_service.clear_history(customer_id)

    state = run_router(
        customer_id=customer_id,
        message="What's the status of my ticket?",
    )

    check("needs_clarification is True (no ticket ID anywhere)",
          state.needs_clarification is True)
    check("execution was skipped",
          state.tool_used is None)
    check("clarification response populated",
          bool(state.response))

    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 10 — Shared Memory & Conversation Context")
    print("=" * 60)

    try:
        validate_memory_retrieval_flow()
        validate_fresh_customer_no_memory()
        validate_history_accumulation()
        validate_no_ticket_in_history()

        print("\n" + "=" * 60)
        print("  Memory loader/writer nodes       ✅")
        print("  History persisted per customer   ✅")
        print("  ticket_id recovered from memory  ✅")
        print("  Multi-turn conversation works    ✅")
        print("  Fresh customer unaffected        ✅")
        print("  History accumulation correct     ✅")
        print("  Clarification when no history    ✅")
        print("  Isolated requests → Conversations ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()