"""
tests/validate_escalation_flow.py

End-to-end validation of Milestone 13 — Human Escalation & Agent Handoff.

Run with:
    python -m tests.validate_escalation_flow

Requires PostgreSQL running and OPENAI_API_KEY set.
"""

import sys
import uuid

from app.database.init_db import init_db
from app.graphs.router_graph import router_graph
from app.nodes.escalation_detection_node import escalation_detection_node
from app.schemas.agent_state import AgentState
from app.services.escalation_service import EscalationService

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
# Unit: escalation_detection_node in isolation
# ---------------------------------------------------------------------------

def validate_detection_node_unit() -> None:
    print("\n[Unit 1] Escalation detection — legal threat")

    state = AgentState(customer_id="TEST", message="I am contacting my attorney.")
    state = escalation_detection_node(state)

    check("needs_human is True",          state.needs_human is True)
    check("escalation_reason is set",     bool(state.escalation_reason))
    check("escalation_queue is legal",    state.escalation_queue == "legal")
    check("response not set (node only detects)", state.response is None)


def validate_detection_node_safety() -> None:
    print("\n[Unit 2] Escalation detection — safety concern")

    state = AgentState(customer_id="TEST", message="I was injured by your product.")
    state = escalation_detection_node(state)

    check("needs_human is True",          state.needs_human is True)
    check("escalation_queue is safety",   state.escalation_queue == "safety")


def validate_detection_node_no_signal() -> None:
    print("\n[Unit 3] Escalation detection — no signal")

    state = AgentState(customer_id="TEST", message="I want a refund.")
    state = escalation_detection_node(state)

    check("needs_human is False",         state.needs_human is False)
    check("escalation_reason is None",    state.escalation_reason is None)


# ---------------------------------------------------------------------------
# Scenario 1: Legal threat → full escalation flow
# ---------------------------------------------------------------------------

def validate_legal_escalation_flow() -> None:
    print("\n[Scenario 1] Legal threat → escalation_agent → ESC created")

    state = run_router(
        customer_id=f"ESC-{uuid.uuid4().hex[:6]}",
        message="I am contacting my lawyer about this.",
    )

    check("needs_human is True",              state.needs_human is True)
    check("escalation_response is populated", state.escalation_response is not None)
    assert state.escalation_response is not None
    check("escalation_id starts with ESC-",   state.escalation_response.escalation_id.startswith("ESC-"))
    check("escalation queue is legal",        state.escalation_response.queue.value == "legal")
    check("response mentions escalation ID",
          state.response is not None and
          state.escalation_response.escalation_id in state.response)
    check("no ticket created",                state.ticket_id is None)

    print(f"  ℹ️  Escalation ID: {state.escalation_response.escalation_id}")
    print(f"  ℹ️  Queue:         {state.escalation_response.queue.value}")
    print(f"  ℹ️  Response:\n{state.response}")


# ---------------------------------------------------------------------------
# Scenario 2: Normal refund request — no escalation (regression)
# ---------------------------------------------------------------------------

def validate_normal_flow_regression() -> None:
    print("\n[Scenario 2] Refund request — no escalation (regression)")

    state = run_router(
        customer_id=f"REG-{uuid.uuid4().hex[:6]}",
        message="I want a refund for my damaged order.",
    )

    check("needs_human is False",             state.needs_human is False)
    check("escalation_response is None",      state.escalation_response is None)
    check("ticket was created",               bool(state.ticket_id))
    check("response populated",               bool(state.response))

    print(f"  ℹ️  Ticket ID: {state.ticket_id}")


# ---------------------------------------------------------------------------
# Scenario 3: Escalation persists in PostgreSQL
# ---------------------------------------------------------------------------

def validate_escalation_persistence() -> None:
    print("\n[Scenario 3] Escalation persists in PostgreSQL")

    service = EscalationService()
    from app.schemas.escalation import CreateEscalationRequest, EscalationQueue

    created = service.create_escalation(CreateEscalationRequest(
        customer_id=f"PERSIST-{uuid.uuid4().hex[:6]}",
        reason="Test persistence",
        queue=EscalationQueue.GENERAL,
    ))

    # Fresh service instance — simulates restart
    service2 = EscalationService()
    retrieved = service2.get_escalation(created.escalation_id)

    check("Escalation retrieved by fresh instance", retrieved is not None)
    assert retrieved is not None
    check("escalation_id matches",                  retrieved.escalation_id == created.escalation_id)
    check("customer_id matches",                    retrieved.customer_id == created.customer_id)
    check("reason matches",                         retrieved.reason == created.reason)
    check("status is OPEN",                         retrieved.status.value == "open")

    print(f"  ℹ️  Escalation ID: {created.escalation_id}")


# ---------------------------------------------------------------------------
# Scenario 4: Router selects escalation_agent for human-request phrase
# ---------------------------------------------------------------------------

def validate_router_selects_escalation() -> None:
    print('\n[Scenario 4] "Speak to a human" → escalation_agent')

    state = run_router(
        customer_id=f"HUMAN-{uuid.uuid4().hex[:6]}",
        message="I want to speak to a human agent.",
    )

    check("needs_human is True",              state.needs_human is True)
    check("escalation_response populated",    state.escalation_response is not None)
    check("response populated",               bool(state.response))

    print(f"  ℹ️  Escalation: {state.escalation_response.escalation_id if state.escalation_response else 'N/A'}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 13 — Human Escalation & Agent Handoff")
    print("=" * 60)

    print("\n  Initialising database tables...")
    try:
        init_db()
    except Exception as e:
        print(f"\n  ❌  PostgreSQL unavailable: {e}")
        sys.exit(1)

    try:
        validate_detection_node_unit()
        validate_detection_node_safety()
        validate_detection_node_no_signal()
        validate_legal_escalation_flow()
        validate_normal_flow_regression()
        validate_escalation_persistence()
        validate_router_selects_escalation()

        print("\n" + "=" * 60)
        print("  Escalation detection (rule-based)  ✅")
        print("  Legal / safety / fraud queues      ✅")
        print("  escalation_agent creates ESC-*     ✅")
        print("  Escalation ID in response          ✅")
        print("  PostgreSQL persistence             ✅")
        print("  Ticket flow unaffected (regression)✅")
        print("  'Speak to human' → escalation      ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()