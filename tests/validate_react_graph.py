"""
tests/validate_react_graph.py

End-to-end validation of the ReAct graph.

Validates that state evolves correctly across all three nodes:
    llm_decision_node → tool_executor_node → response_node

Each scenario inspects the final AgentState to confirm:
    - The correct fields were populated by the correct nodes.
    - No prior state was lost or mutated unexpectedly.
    - The response node produced output (or escalated) appropriately.

This script calls the real OpenAI API.
Requires OPENAI_API_KEY to be set in your .env file.

Run with:
    python -m tests.validate_react_graph
"""

import sys

from app.graphs.react_graph import react_graph
from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import NO_TOOL

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


def run_graph(customer_id: str, message: str) -> AgentState:
    """
    Invoke the react_graph and return the final AgentState.

    react_graph.invoke() accepts a dict matching AgentState fields
    and returns the final state dict. We reconstruct AgentState
    from that dict for typed field access in assertions.
    """
    result = react_graph.invoke({
        "customer_id": customer_id,
        "message":     message,
    })
    # LangGraph returns a dict — reconstruct as AgentState for typed access.
    return AgentState(**result)


# ---------------------------------------------------------------------------
# Scenario 1: Customer requests a refund
#
# Expected state evolution:
#   llm_decision_node  → tool_decision.tool_name = "create_ticket_tool"
#   tool_executor_node → tool_used = "create_ticket_tool", tool_result = TicketResponse
#   response_node      → response contains ticket ID, needs_human = False
# ---------------------------------------------------------------------------

def validate_refund_request() -> None:
    print("\n[Scenario 1] Refund Request — 'I want a refund.'")

    state = run_graph(customer_id="C001", message="I want a refund.")

    # llm_decision_node output
    check("tool_decision is populated",
          state.tool_decision is not None)

    # Explicit None guard for Pylance type narrowing.
    # check() above already asserts this — the guard makes the narrowing
    # explicit so Pylance can track it through subsequent attribute access.
    assert state.tool_decision is not None

    check("LLM chose create_ticket_tool",
          state.tool_decision.tool_name == "create_ticket_tool")
    check("tool_decision has reasoning",
          bool(state.tool_decision.reasoning))
    check("tool_decision is not no_tool",
          not state.tool_decision.is_no_tool())

    # tool_executor_node output
    check("tool_used is populated",
          state.tool_used is not None)
    check("tool_used matches decision",
          state.tool_used == state.tool_decision.tool_name)
    check("tool_result is populated",
          state.tool_result is not None)
    check("tool_result has ticket_id",
          bool(getattr(state.tool_result, "ticket_id", None)))

    # response_node output
    check("response is populated",
          bool(state.response))
    check("ticket_id extracted into state",
          bool(state.ticket_id))
    check("ticket_id in state matches tool_result",
          state.ticket_id == state.tool_result.ticket_id)  # type: ignore
    check("needs_human is False on success",
          state.needs_human is False)

    # State preservation — prior node contributions must survive
    check("tool_decision preserved after executor ran",
          state.tool_decision is not None)
    check("extracted_arguments populated by extraction node",
          state.extracted_arguments is not None)
    check("tool_result not mutated (still a TicketResponse)",
          hasattr(state.tool_result, "ticket_id"))

    print(f"  ℹ️  Ticket ID: {state.ticket_id}")
    print(f"  ℹ️  LLM reasoning: {state.tool_decision.reasoning}")  # narrowed above
    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Scenario 2: Customer sends a greeting
#
# Expected state evolution:
#   llm_decision_node  → tool_decision.tool_name = "no_tool"
#   tool_executor_node → skips execution, tool_used = None, tool_result = None
#   response_node      → clarification message, needs_human = False
# ---------------------------------------------------------------------------

def validate_greeting() -> None:
    print("\n[Scenario 2] Greeting — 'Hello'")

    state = run_graph(customer_id="C002", message="Hello")

    # llm_decision_node output
    check("tool_decision is populated",
          state.tool_decision is not None)
    assert state.tool_decision is not None  # Pylance narrowing

    check("LLM chose no_tool",
          state.tool_decision.tool_name == NO_TOOL)
    check("tool_decision.is_no_tool() returns True",
          state.tool_decision.is_no_tool())

    # tool_executor_node output — should have skipped execution
    check("tool_used is None (no tool executed)",
          state.tool_used is None)
    check("tool_result is None (no execution happened)",
          state.tool_result is None)
    check("ticket_id is None",
          state.ticket_id is None)

    # response_node output
    check("response is populated",
          bool(state.response))
    check("needs_human is False for greeting",
          state.needs_human is False)

    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Scenario 3: Delivery issue — confirms ticket created for non-refund issues
# ---------------------------------------------------------------------------

def validate_delivery_issue() -> None:
    print("\n[Scenario 3] Delivery Issue — 'My package never arrived.'")

    state = run_graph(customer_id="C003", message="My package never arrived.")

    check("tool_decision is populated",           state.tool_decision is not None)
    assert state.tool_decision is not None  # Pylance narrowing
    check("LLM chose create_ticket_tool",         state.tool_decision.tool_name == "create_ticket_tool")
    check("tool_result is populated",             state.tool_result is not None)
    check("ticket_id is assigned",                bool(state.ticket_id))
    check("response is populated",                bool(state.response))
    check("needs_human is False",                 state.needs_human is False)

    print(f"  ℹ️  Ticket ID: {state.ticket_id}")


# ---------------------------------------------------------------------------
# Scenario 4: State completeness check
#
# Confirms the final state after a successful run is a complete,
# non-destructive record — no node overwrote another's contribution.
# ---------------------------------------------------------------------------

def validate_state_completeness() -> None:
    print("\n[Scenario 4] State Completeness — all node contributions preserved")

    state = run_graph(customer_id="C004", message="I was charged twice.")

    # Every node's output must coexist in the final state.
    check("tool_decision (from llm_decision_node) present",        state.tool_decision is not None)
    assert state.tool_decision is not None  # Pylance narrowing
    check("extracted_arguments (from extraction node) present",    state.extracted_arguments is not None)
    check("tool_used (from tool_executor_node) present",           state.tool_used is not None)
    check("tool_result (from tool_executor_node) present",         state.tool_result is not None)
    check("response (from response_node) present",                 bool(state.response))
    check("ticket_id (from response_node) present",                bool(state.ticket_id))

    # Input fields must be untouched
    check("customer_id unchanged",    state.customer_id == "C004")
    check("message unchanged",        state.message == "I was charged twice.")

    print(f"  ℹ️  State fields populated: tool_decision ✓ extracted_arguments ✓ "
          f"tool_used ✓ tool_result ✓ response ✓ ticket_id ✓")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  ReAct Graph — End-to-End Validation")
    print("  Reason → Act → Observe → Respond")
    print("=" * 60)

    try:
        validate_refund_request()
        validate_greeting()
        validate_delivery_issue()
        validate_state_completeness()

        print("\n" + "=" * 60)
        print("  llm_decision_node   ✅  (Reason)")
        print("  tool_executor_node  ✅  (Act + Observe)")
        print("  response_node       ✅  (Respond)")
        print("  State Evolution     ✅  (non-destructive across nodes)")
        print("  ReAct Loop          ✅  complete")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()