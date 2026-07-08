"""
ticket.py

Purpose:
--------
Define ticket-related data contracts used across the platform.

Responsibilities:
-----------------
- Validate ticket creation requests
- Standardize ticket responses
- Define ticket status values
- Provide typed interfaces between layers

This module DOES NOT:
---------------------
- Create tickets
- Store tickets in databases
- Execute business logic
- Call external services
- Interact with agents
- Manage workflows

Architecture Philosophy:
------------------------
Schemas represent contracts, not behavior.
Business logic belongs to services and agents.
Keeping schemas pure makes the system easier to test,
maintain, and evolve.
"""

from enum import Enum

from pydantic import BaseModel


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class CreateTicketRequest(BaseModel):
    customer_id: str
    issue: str


class TicketResponse(BaseModel):
    ticket_id: str
    customer_id: str
    issue: str
    status: TicketStatus
    agent_response: str | None = None
    

class UpdateTicketRequest(BaseModel):
    """
    Schema for partially updating an existing ticket.

    All fields are optional — only the fields provided will be applied.
    Fields left as None mean "do not change this value."

    What callers CAN update:
        - status:         Move the ticket through its lifecycle (OPEN → IN_PROGRESS → RESOLVED).
        - agent_response: The agent's reply to the customer's issue.

    What callers CANNOT update (intentionally absent):
        - ticket_id:    Immutable. Set once by the service at creation.
        - customer_id:  Immutable. Belongs to the original request.
        - issue:        Immutable. The customer's original message should not be altered.
    """

    status: TicketStatus | None = None
    agent_response: str | None = None