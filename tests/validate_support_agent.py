"""
scripts/validate_support_agent.py

Validation script for the SupportAgent layer.

Verifies:
    - Intent detection for all four supported intents.
    - Correct tool is called (or not called) per intent.
    - Ticket is created where expected.
    - AgentResponse is always structured (never a raw string).
    - General inquiry produces no ticket and no tool call.

Runs without FastAPI, PostgreSQL, or OpenAI.
This confirms that the Agent, Tool, Service, and Schema layers
are correctly wired together in isolation.

Run with:
    python -m scripts.validate_support_agent
"""

from app.agents.support_agent import SupportAgent
from app.schemas.agent import AgentResponse, Intent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"

agent = SupportAgent()


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


def run_case(message: str, customer_id: str = "C001") -> AgentResponse:
    """
    Run a single message through the agent and return the response.
    Confirms the return type is always AgentResponse (never a raw string).
    """
    response = agent.handle_message(customer_id=customer_id, message=message)
    check(
        f"Response is AgentResponse (not a raw string or dict)",
        isinstance(response, AgentResponse),
    )
    return response


# ---------------------------------------------------------------------------
# Case 1: Refund Request
# ---------------------------------------------------------------------------

def validate_refund_request() -> None:
    print("\n[Case 1] Refund Request — 'I want a refund'")

    response = run_case("I want a refund")

    check("Intent is REFUND_REQUEST",               response.intent == Intent.REFUND_REQUEST)
    check("Tool used is create_ticket_tool",        response.tool_used == "create_ticket_tool")
    check("Ticket ID is assigned",                  bool(response.ticket_id))
    check("Response text is not empty",             bool(response.response))
    check("needs_human is False",                   response.needs_human is False)


# ---------------------------------------------------------------------------
# Case 2: Delivery Issue
# ---------------------------------------------------------------------------

def validate_delivery_issue() -> None:
    print("\n[Case 2] Delivery Issue — 'My package never arrived'")

    # "never arrived" is an explicit delivery keyword.
    # Avoid "My package was not delivered" here since "delivered" was
    # removed from _DELIVERY_KEYWORDS to prevent false matches on
    # order-issue messages like "The wrong item was delivered".
    response = run_case("My package never arrived")

    check("Intent is DELIVERY_ISSUE",               response.intent == Intent.DELIVERY_ISSUE)
    check("Tool used is create_ticket_tool",        response.tool_used == "create_ticket_tool")
    check("Ticket ID is assigned",                  bool(response.ticket_id))
    check("Response text is not empty",             bool(response.response))


# ---------------------------------------------------------------------------
# Case 3: Order Issue
# ---------------------------------------------------------------------------

def validate_order_issue() -> None:
    print("\n[Case 3] Order Issue — 'The wrong item was delivered'")

    response = run_case("The wrong item was delivered")

    check("Intent is ORDER_ISSUE",                  response.intent == Intent.ORDER_ISSUE)
    check("Tool used is create_ticket_tool",        response.tool_used == "create_ticket_tool")
    check("Ticket ID is assigned",                  bool(response.ticket_id))
    check("Response text is not empty",             bool(response.response))


# ---------------------------------------------------------------------------
# Case 4: General Inquiry
# ---------------------------------------------------------------------------

def validate_general_inquiry() -> None:
    print("\n[Case 4] General Inquiry — 'Hello'")

    response = run_case("Hello")

    check("Intent is GENERAL_INQUIRY",              response.intent == Intent.GENERAL_INQUIRY)
    check("No tool used",                           response.tool_used is None)
    check("No ticket created",                      response.ticket_id is None)
    check("Response text is not empty",             bool(response.response))


# ---------------------------------------------------------------------------
# Case 5: Edge cases — keywords appear in different contexts
# ---------------------------------------------------------------------------

def validate_edge_cases() -> None:
    print("\n[Case 5] Edge Cases")

    # Refund keyword takes priority over delivery keyword in same message.
    response = run_case("My delivery was wrong and I want a refund")
    check(
        "Refund takes priority over delivery when both keywords present",
        response.intent == Intent.REFUND_REQUEST,
    )

    # Case-insensitive matching.
    response = run_case("I WANT A REFUND PLEASE")
    check(
        "Intent detection is case-insensitive",
        response.intent == Intent.REFUND_REQUEST,
    )

    # Empty-ish message falls back to general inquiry.
    response = run_case("   ")
    check(
        "Whitespace-only message falls back to GENERAL_INQUIRY",
        response.intent == Intent.GENERAL_INQUIRY,
    )

    # Each call produces a unique ticket ID (no ID collision).
    r1 = run_case("I want a refund", customer_id="C010")
    r2 = run_case("I want a refund", customer_id="C011")
    check(
        "Two separate calls produce distinct ticket IDs",
        r1.ticket_id != r2.ticket_id,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  Milestone 1 — SupportAgent Validation")
    print("=" * 55)

    try:
        validate_refund_request()
        validate_delivery_issue()
        validate_order_issue()
        validate_general_inquiry()
        validate_edge_cases()

        print("\n" + "=" * 55)
        print("  Schema Layer   ✅")
        print("  Service Layer  ✅")
        print("  Tool Layer     ✅")
        print("  Agent Layer    ✅")
        print("=" * 55)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()