"""
tests/validate_router_graph.py

End-to-end validation of Milestone 9 — Agent Routing & Specialist Agents.

Validates the full multi-agent flow:
    router_node → agent_dispatch_node → specialist agent → response

Key contracts tested:
    - Router selects the correct agent for different message types.
    - ticket_agent runs its full pipeline (decision → extraction → validation → execution → response).
    - faq_agent stub returns its not-implemented response.
    - routing_decision is preserved in final state.
    - All prior milestones still work through the new router layer (regression).

Run with:
    python -m tests.validate_router_graph
"""

import sys

from app.graphs.router_graph import router_graph
from app.schemas.agent_state import AgentState
from app.tools.ticket_tools import create_ticket_tool

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
# Scenario 1: Refund request → ticket_agent → ticket created
# ---------------------------------------------------------------------------

def validate_ticket_agent_routing() -> None:
    print("\n[Scenario 1] Refund request → routed to ticket_agent")

    state = run_router(customer_id="C001", message="I want a refund for my order.")

    # Routing layer
    check("routing_decision is populated",
          state.routing_decision is not None)
    assert state.routing_decision is not None

    check("Router selected ticket_agent",
          state.routing_decision.agent_name == "ticket_agent")
    check("routing_decision has reasoning",
          bool(state.routing_decision.reasoning))

    # Ticket agent pipeline ran
    check("tool_decision is populated (ticket agent ran LLM decision)",
          state.tool_decision is not None)
    check("ticket was created",
          bool(state.ticket_id))
    check("response is populated",
          bool(state.response))
    check("needs_human is False",
          state.needs_human is False)

    print(f"  ℹ️  Routed to: {state.routing_decision.agent_name}")
    print(f"  ℹ️  Ticket ID: {state.ticket_id}")
    print(f"  ℹ️  Response: {state.response is not None and state.response[:80]}...")


# ---------------------------------------------------------------------------
# Scenario 2: FAQ question → faq_agent stub
# ---------------------------------------------------------------------------

def validate_faq_agent_routing() -> None:
    print("\n[Scenario 2] FAQ question → routed to faq_agent")

    state = run_router(
        customer_id="C002",
        message="What is your return policy?",
    )

    check("routing_decision is populated",
          state.routing_decision is not None)
    assert state.routing_decision is not None

    check("Router selected faq_agent",
          state.routing_decision.agent_name == "faq_agent")
    check("response is populated",
          bool(state.response))
    check("faq stub response mentions help center or ticket",
        state.response is not None and (
            "faq" in state.response.lower()
            or "help" in state.response.lower()
            or "ticket" in state.response.lower()
        ))

    print(f"  ℹ️  Routed to: {state.routing_decision.agent_name}")
    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Scenario 3: Ticket lookup through router → ticket_agent handles retrieval
# ---------------------------------------------------------------------------

def validate_ticket_lookup_through_router() -> None:
    print("\n[Scenario 3] Ticket status request → ticket_agent → get_ticket_tool")

    created = create_ticket_tool(customer_id="C003", issue="Wrong item delivered.")
    ticket_id = created.ticket_id

    state = run_router(
        customer_id="C003",
        message=f"What's the status of {ticket_id}?",
    )

    assert state.routing_decision is not None
    check("Router selected ticket_agent",
          state.routing_decision.agent_name == "ticket_agent")
    check("extracted ticket_id matches",
          state.extracted_arguments is not None and
          state.extracted_arguments.get("ticket_id") == ticket_id)
    check("tool_used is get_ticket_tool",
          state.tool_used == "get_ticket_tool")
    # After
    check("response contains ticket ID",
        state.response is not None and ticket_id in state.response)

    print(f"  ℹ️  Ticket ID: {ticket_id}")
    print(f"  ℹ️  Response:\n{state.response}")


# ---------------------------------------------------------------------------
# Scenario 4: Ambiguous ticket request (no ID) → clarification through router
# ---------------------------------------------------------------------------

def validate_clarification_through_router() -> None:
    print("\n[Scenario 4] Ambiguous ticket request → clarification through router")

    state = run_router(
        customer_id="C004",
        message="What is the status of my ticket?",
    )

    assert state.routing_decision is not None
    check("Router selected ticket_agent",
          state.routing_decision.agent_name == "ticket_agent")
    check("needs_clarification is True",
          state.needs_clarification is True)
    check("execution skipped (tool_used is None)",
          state.tool_used is None)
    check("clarification response populated",
          bool(state.response))

    print(f"  ℹ️  Response: {state.response}")


# ---------------------------------------------------------------------------
# Scenario 5: routing_decision preserved in final state
# ---------------------------------------------------------------------------

def validate_routing_decision_preserved() -> None:
    print("\n[Scenario 5] routing_decision preserved after specialist agent runs")

    state = run_router(
        customer_id="C005",
        message="I was charged twice for my order.",
    )

    check("routing_decision still present after ticket_agent ran",
          state.routing_decision is not None)
    assert state.routing_decision is not None
    check("agent_name still ticket_agent",
          state.routing_decision.agent_name == "ticket_agent")
    check("customer_id unchanged",
          state.customer_id == "C005")
    check("ticket created",
          bool(state.ticket_id))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 9 — Agent Routing & Specialist Agents")
    print("=" * 60)

    try:
        validate_ticket_agent_routing()
        validate_faq_agent_routing()
        validate_ticket_lookup_through_router()
        validate_clarification_through_router()
        validate_routing_decision_preserved()

        print("\n" + "=" * 60)
        print("  Router node                  ✅")
        print("  ticket_agent routing         ✅")
        print("  faq_agent stub routing       ✅")
        print("  Ticket retrieval via router  ✅")
        print("  Clarification via router     ✅")
        print("  routing_decision preserved   ✅")
        print("  Multi-agent platform         ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()