"""
app/api/dependencies.py

Purpose:
--------
Define FastAPI dependency providers for all application services.

Responsibilities:
-----------------
- Provide TicketService, ConversationService, and RouterService
  instances via FastAPI's Depends() mechanism.
- Be the single place to swap implementations for testing or
  different deployment environments.

This module DOES NOT:
---------------------
- Contain business logic.
- Call the database directly.
- Know about agents or graph internals.

Why dependency injection instead of module-level singletons?
------------------------------------------------------------
Global singletons:
    from app.services.ticket_service import ticket_service
    # Hard to mock in tests
    # Can't swap implementations per environment
    # Can't scope resources per request

FastAPI DI:
    service: TicketService = Depends(get_ticket_service)
    # Tests override with: app.dependency_overrides[get_ticket_service] = lambda: FakeTicketService()
    # Implementations swappable per environment
    # Future: request-scoped session injection here

The functions are intentionally simple today.
Their value is the injection point they provide — not their complexity.

Testing example:
----------------
    def test_create_ticket():
        app.dependency_overrides[get_ticket_service] = lambda: FakeTicketService()
        response = client.post("/tickets", json={...})
        assert response.status_code == 200
"""

from app.services.conversation_service import ConversationService
from app.services.router_service import RouterService
from app.services.ticket_service import TicketService


def get_ticket_service() -> TicketService:
    """
    Provide a TicketService instance.

    Returns a new instance per call — stateless since all state
    is in PostgreSQL. When caching or connection pooling is needed,
    this is the only place to add it.
    """
    return TicketService()


def get_conversation_service() -> ConversationService:
    """
    Provide a ConversationService instance.
    """
    return ConversationService()


def get_router_service() -> RouterService:
    """
    Provide a RouterService instance — the application entry point.
    """
    return RouterService()