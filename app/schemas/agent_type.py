"""
app/schemas/agent_type.py

Purpose:
--------
Define the AgentType enum — the canonical set of specialist agents
the router can dispatch to.

Adding a new agent:
    1. Add an entry here.
    2. Add a stub or full graph to AGENT_REGISTRY.
    3. Update the router prompt.
    No other files change.
"""

from enum import Enum


class AgentType(str, Enum):
    TICKET = "ticket_agent"
    ORDER  = "order_agent"
    FAQ    = "faq_agent"