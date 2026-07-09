"""
app/schemas/agent.py

Purpose:
--------
Define contracts exchanged between the agent layer and the rest
of the platform.

Responsibilities:
-----------------
- Standardize agent outputs
- Define supported intents
- Provide typed responses for APIs and workflows

This module DOES NOT:
---------------------
- Execute tools
- Detect intents
- Manage workflows
- Store memory
- Call LLMs

Architecture Philosophy:
------------------------
Agents should return structured state, not raw text.
Structured outputs make workflows predictable,
testable, and easier to evolve.
"""

from enum import Enum

from pydantic import BaseModel


class Intent(str, Enum):
    GENERAL_INQUIRY = "general_inquiry"
    REFUND_REQUEST = "refund_request"
    DELIVERY_ISSUE = "delivery_issue"
    ORDER_ISSUE = "order_issue"


class AgentResponse(BaseModel):
    intent: Intent
    response: str
    tool_used: str | None = None
    ticket_id: str | None = None
    needs_human: bool = False