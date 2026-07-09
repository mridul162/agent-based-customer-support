"""
tests/validate_ticket_tools.py

Validation script for Milestone 1 — Tool, Service, and Schema layers.

Runs without FastAPI, database, or OpenAI.
This is intentional: business logic should be testable in isolation.

Run with:
    python -m tests.validate_ticket_tools

Expected outcome:
    Tool Layer   ✅
    Service Layer ✅
    Schema Layer  ✅
"""

from app.schemas.ticket import TicketStatus
from app.tools.ticket_tools import (
    create_ticket_tool,
    get_ticket_tool,
    list_tickets_tool,
    update_ticket_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    if not condition:
        raise AssertionError(f"Validation failed: {label}")


# ---------------------------------------------------------------------------
# Validation 1: Create a ticket and retrieve it
# Validates: create_ticket_tool, get_ticket_tool, schema roundtrip
# ---------------------------------------------------------------------------

def validate_create_and_retrieve() -> None:
    print("\n[1] Create and Retrieve")

    ticket = create_ticket_tool(
        customer_id="C001",
        issue="Refund request",
    )

    check("Ticket is not None",                     ticket is not None)
    check("ticket_id is assigned",                  bool(ticket.ticket_id))
    check("customer_id matches",                    ticket.customer_id == "C001")
    check("issue matches",                          ticket.issue == "Refund request")
    check("Initial status is OPEN",                 ticket.status == TicketStatus.OPEN)
    check("agent_response is None on creation",     ticket.agent_response is None)

    # Core validation from the mentor: get_ticket_tool must return the same object.
    retrieved = get_ticket_tool(ticket.ticket_id)

    check("Retrieved ticket is not None",           retrieved is not None)
    check("ticket_id matches",                      retrieved.ticket_id == ticket.ticket_id) # type: ignore
    check("customer_id matches",                    retrieved.customer_id == ticket.customer_id) # type: ignore
    check("issue matches",                          retrieved.issue == ticket.issue) # type: ignore
    check("status matches",                         retrieved.status == ticket.status) # type: ignore


# ---------------------------------------------------------------------------
# Validation 2: Retrieve a ticket that does not exist
# Validates: get_ticket_tool returns None (not an exception)
# ---------------------------------------------------------------------------

def validate_missing_ticket() -> None:
    print("\n[2] Retrieve Non-Existent Ticket")

    result = get_ticket_tool("TICKET-DOESNOTEXIST")

    check("Returns None for missing ticket",        result is None)


# ---------------------------------------------------------------------------
# Validation 3: Update a ticket's status and agent_response
# Validates: update_ticket_tool, partial update logic, status transitions
# ---------------------------------------------------------------------------

def validate_update() -> None:
    print("\n[3] Update Ticket")

    ticket = create_ticket_tool(
        customer_id="C002",
        issue="Order never arrived",
    )

    # Partial update: status only
    updated = update_ticket_tool(
        ticket_id=ticket.ticket_id,
        status=TicketStatus.IN_PROGRESS,
    )

    check("Updated ticket is not None",             updated is not None)
    check("Status updated to IN_PROGRESS",          updated.status == TicketStatus.IN_PROGRESS) # type: ignore
    check("agent_response still None",              updated.agent_response is None) # type: ignore
    check("customer_id unchanged",                  updated.customer_id == "C002") # type: ignore
    check("issue unchanged",                        updated.issue == "Order never arrived") # type: ignore

    # Partial update: agent_response only
    updated = update_ticket_tool(
        ticket_id=ticket.ticket_id,
        agent_response="We are investigating your missing order.",
    )

    check("agent_response set correctly",
          updated.agent_response == "We are investigating your missing order.") # type: ignore
    check("Status still IN_PROGRESS after response update",
          updated.status == TicketStatus.IN_PROGRESS) # type: ignore

    # Full resolution
    updated = update_ticket_tool(
        ticket_id=ticket.ticket_id,
        status=TicketStatus.RESOLVED,
    )

    check("Status updated to RESOLVED",             updated.status == TicketStatus.RESOLVED) # type: ignore


# ---------------------------------------------------------------------------
# Validation 4: Update a ticket that does not exist
# Validates: update_ticket_tool returns None (not an exception)
# ---------------------------------------------------------------------------

def validate_update_missing_ticket() -> None:
    print("\n[4] Update Non-Existent Ticket")

    result = update_ticket_tool(
        ticket_id="TICKET-DOESNOTEXIST",
        status=TicketStatus.RESOLVED,
    )

    check("Returns None for missing ticket",        result is None)


# ---------------------------------------------------------------------------
# Validation 5: List all tickets
# Validates: list_tickets_tool, multiple ticket state consistency
# ---------------------------------------------------------------------------

def validate_list() -> None:
    print("\n[5] List Tickets")

    # Note: tickets created in earlier validations are in the same
    # module-level service instance — this is expected in-memory behaviour.
    all_tickets = list_tickets_tool()

    check("Returns a list",                         isinstance(all_tickets, list))
    check("At least 2 tickets exist from prior steps",  len(all_tickets) >= 2)

    for ticket in all_tickets:
        check(
            f"Ticket {ticket.ticket_id} has a valid ticket_id",
            bool(ticket.ticket_id),
        )
        check(
            f"Ticket {ticket.ticket_id} has a valid customer_id",
            bool(ticket.customer_id),
        )
        check(
            f"Ticket {ticket.ticket_id} has a valid status",
            isinstance(ticket.status, TicketStatus),
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  Milestone 1 — Layer Validation")
    print("=" * 55)

    try:
        validate_create_and_retrieve()
        validate_missing_ticket()
        validate_update()
        validate_update_missing_ticket()
        validate_list()

        print("\n" + "=" * 55)
        print("  Schema Layer   ✅")
        print("  Service Layer  ✅")
        print("  Tool Layer     ✅")
        print("=" * 55)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()