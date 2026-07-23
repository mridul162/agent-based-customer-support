"""
app/schemas/escalation.py

Purpose:
--------
Define the data contracts for customer escalations.

Mirrors the ticket schema pattern exactly:
    EscalationStatus  → TicketStatus
    CreateEscalationRequest → CreateTicketRequest
    EscalationResponse      → TicketResponse

This module DOES NOT:
---------------------
- Create escalations (EscalationService owns that).
- Know about agents, nodes, or graph execution.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EscalationStatus(str, Enum):
    OPEN        = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED    = "resolved"


class EscalationQueue(str, Enum):
    """Which human team receives this escalation."""
    GENERAL  = "general"
    LEGAL    = "legal"
    SAFETY   = "safety"
    BILLING  = "billing"


class CreateEscalationRequest(BaseModel):
    customer_id: str
    reason:      str
    queue:       EscalationQueue = EscalationQueue.GENERAL


class EscalationResponse(BaseModel):
    escalation_id: str
    customer_id:   str
    reason:        str
    queue:         EscalationQueue
    status:        EscalationStatus
    created_at:    datetime | None = None