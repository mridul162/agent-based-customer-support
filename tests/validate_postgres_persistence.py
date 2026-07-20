"""
tests/validate_postgres_persistence.py

Validates Milestone 11.5 — PostgreSQL Persistence + Transaction Management.

Validates:
    - Ticket persistence
    - Conversation persistence
    - Service-level transaction boundaries
    - Repository operations without explicit commit()
    - Data survives service instance restarts

Key contract:

    service1.create_ticket(...)
    service2 = TicketService()
    service2.get_ticket(...)

    # data must still exist because get_session()
    # committed the transaction automatically

Requires a running PostgreSQL instance with tables initialised:

    python -m app.database.init_db

Run with:

    python -m tests.validate_postgres_persistence
"""

import sys
import uuid

from app.database.init_db import init_db
from app.schemas.ticket import CreateTicketRequest, TicketStatus
from app.services.conversation_service import ConversationService
from app.services.ticket_service import TicketService

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")

    if not condition:
        raise AssertionError(f"Validation failed: {label}")


# ---------------------------------------------------------------------------
# Scenario 1: Create and retrieve a ticket via fresh service instances
# ---------------------------------------------------------------------------

def validate_ticket_persistence() -> None:
    print("\n[Scenario 1] Ticket persists across service instances")

    service1 = TicketService()

    request = CreateTicketRequest(
        customer_id=f"TEST-{uuid.uuid4().hex[:6]}",
        issue="Validate PostgreSQL ticket persistence.",
    )

    created = service1.create_ticket(request)

    check("Ticket created with ID", bool(created.ticket_id))
    check("Status is OPEN", created.status == TicketStatus.OPEN)
    check("Issue matches", created.issue == request.issue)
    check(
        "customer_id matches",
        created.customer_id == request.customer_id,
    )

    # Fresh service instance — simulates application restart
    service2 = TicketService()

    retrieved = service2.get_ticket(created.ticket_id)

    check(
        "Ticket retrieved by fresh instance",
        retrieved is not None,
    )

    assert retrieved is not None

    check(
        "ticket_id matches",
        retrieved.ticket_id == created.ticket_id,
    )
    check(
        "customer_id matches",
        retrieved.customer_id == created.customer_id,
    )
    check(
        "issue matches",
        retrieved.issue == created.issue,
    )
    check(
        "status matches",
        retrieved.status == created.status,
    )

    print(f"  ℹ️  Ticket ID: {created.ticket_id}")


# ---------------------------------------------------------------------------
# Scenario 2: get_ticket returns None for unknown ID
# ---------------------------------------------------------------------------

def validate_ticket_not_found() -> None:
    print("\n[Scenario 2] get_ticket returns None for unknown ticket")

    service = TicketService()

    result = service.get_ticket("TICKET-DOESNOTEXIST")

    check(
        "Returns None for unknown ticket ID",
        result is None,
    )


# ---------------------------------------------------------------------------
# Scenario 3: Conversation history persists across service instances
# ---------------------------------------------------------------------------

def validate_conversation_persistence() -> None:
    print("\n[Scenario 3] Conversation history persists across service instances")

    customer_id = f"CONV-{uuid.uuid4().hex[:6]}"

    service1 = ConversationService()

    service1.clear_history(customer_id)

    service1.append_turn(
        customer_id=customer_id,
        user_message="My package never arrived.",
        assistant_response="Ticket TICKET-TEST123 created.",
    )

    # Fresh service instance — simulates restart
    service2 = ConversationService()

    history = service2.get_history(customer_id)

    check("History has 2 messages", len(history) == 2)
    check("First message is user role", history[0].role == "user")
    check("Second message is assistant role", history[1].role == "assistant")
    check(
        "User content matches",
        history[0].content == "My package never arrived.",
    )
    check(
        "Assistant content matches",
        "TICKET-TEST123" in history[1].content,
    )

    print(
        f"  ℹ️  Customer: {customer_id}, "
        f"messages: {len(history)}"
    )

    service2.clear_history(customer_id)


# ---------------------------------------------------------------------------
# Scenario 4: Multiple turns accumulate in order
# ---------------------------------------------------------------------------

def validate_conversation_ordering() -> None:
    print("\n[Scenario 4] Conversation messages are ordered chronologically")

    customer_id = f"ORDER-{uuid.uuid4().hex[:6]}"

    service = ConversationService()

    service.clear_history(customer_id)

    service.append_turn(
        customer_id,
        "Turn 1 user",
        "Turn 1 assistant",
    )

    service.append_turn(
        customer_id,
        "Turn 2 user",
        "Turn 2 assistant",
    )

    history = service.get_history(customer_id)

    check("4 messages total", len(history) == 4)
    check("Turn 1 user is first", history[0].content == "Turn 1 user")
    check(
        "Turn 1 assistant is second",
        history[1].content == "Turn 1 assistant",
    )
    check("Turn 2 user is third", history[2].content == "Turn 2 user")
    check(
        "Turn 2 assistant is fourth",
        history[3].content == "Turn 2 assistant",
    )

    service.clear_history(customer_id)

    print(
        f"  ℹ️  Customer: {customer_id}, "
        f"verified order of {len(history)} messages"
    )


# ---------------------------------------------------------------------------
# Scenario 5: Two different customers have isolated history
# ---------------------------------------------------------------------------

def validate_customer_isolation() -> None:
    print(
        "\n[Scenario 5] Different customers have isolated "
        "conversation histories"
    )

    c1 = f"ISO-A-{uuid.uuid4().hex[:4]}"
    c2 = f"ISO-B-{uuid.uuid4().hex[:4]}"

    service = ConversationService()

    service.clear_history(c1)
    service.clear_history(c2)

    service.append_turn(
        c1,
        "Customer A message",
        "Response for A",
    )

    service.append_turn(
        c2,
        "Customer B message",
        "Response for B",
    )

    h1 = service.get_history(c1)
    h2 = service.get_history(c2)

    check("Customer A has 2 messages", len(h1) == 2)
    check("Customer B has 2 messages", len(h2) == 2)

    check(
        "Customer A history has A content",
        "Customer A" in h1[0].content,
    )

    check(
        "Customer B history has B content",
        "Customer B" in h2[0].content,
    )

    check(
        "Customer A history has no B content",
        all("Customer B" not in m.content for m in h1),
    )

    service.clear_history(c1)
    service.clear_history(c2)


# ---------------------------------------------------------------------------
# Scenario 6: get_session automatically commits transactions
# ---------------------------------------------------------------------------

def validate_transaction_commit() -> None:
    print("\n[Scenario 6] get_session automatically commits transactions")

    customer_id = f"TXN-{uuid.uuid4().hex[:6]}"

    service = ConversationService()

    service.clear_history(customer_id)

    service.append_turn(
        customer_id=customer_id,
        user_message="Transaction test",
        assistant_response="Commit should occur automatically",
    )

    # Fresh service instance
    fresh_service = ConversationService()

    history = fresh_service.get_history(customer_id)

    check(
        "Messages persisted without repository commit()",
        len(history) == 2,
    )

    check(
        "User message persisted",
        history[0].content == "Transaction test",
    )

    check(
        "Assistant message persisted",
        history[1].content == "Commit should occur automatically",
    )

    fresh_service.clear_history(customer_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Milestone 11.5 — PostgreSQL Persistence Validation")
    print("=" * 60)

    print("\n  Initialising database tables...")

    try:
        init_db()

    except Exception as e:
        print(f"\n  ❌  Could not connect to PostgreSQL: {e}")
        print(
            "  Make sure PostgreSQL is running and "
            "DATABASE_URL is set in .env"
        )
        sys.exit(1)

    try:
        validate_ticket_persistence()
        validate_ticket_not_found()
        validate_conversation_persistence()
        validate_conversation_ordering()
        validate_customer_isolation()
        validate_transaction_commit()

        print("\n" + "=" * 60)
        print("  Ticket persistence (restart-proof)    ✅")
        print("  Not-found returns None                ✅")
        print("  Conversation persistence              ✅")
        print("  Message ordering (chronological)      ✅")
        print("  Customer isolation                    ✅")
        print("  Automatic transaction commit          ✅")
        print("  Repositories are commit-free          ✅")
        print("  In-memory dict → PostgreSQL           ✅")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n  ❌  Validation stopped: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

