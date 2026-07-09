"""
app/schemas/agent_state.py

Purpose:
--------
Represent the state of a single agent execution.

Responsibilities:
-----------------
- Store customer input
- Store detected intent
- Store tool execution results
- Store final response

This module DOES NOT:
---------------------
- Execute agent logic
- Call tools
- Manage memory
- Persist state

Architecture Philosophy:
------------------------
State is the shared language between workflow steps.
Each step reads state and writes state.
"""

from pydantic import BaseModel

from app.schemas.agent import Intent


class AgentState(BaseModel):
    customer_id: str
    message: str

    intent: Intent | None = None

    tool_used: str | None = None
    ticket_id: str | None = None

    response: str | None = None

    needs_human: bool = False