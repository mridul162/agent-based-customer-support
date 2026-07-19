"""
app/schemas/routing_decision.py

Purpose:
--------
Represent the router agent's decision about which specialist agent
should handle the customer's request.

Mirrors ToolDecision in structure — the router makes a selection
decision just as the LLM decision node makes a tool selection decision.
Both return structured output; both carry reasoning for observability.

This module DOES NOT:
---------------------
- Execute routing.
- Know about specific agent implementations.
- Modify AgentState directly.
"""

from pydantic import BaseModel, ConfigDict


class RoutingDecision(BaseModel):
    """
    The router's decision about which specialist agent to invoke.

    Fields:
        agent_name: Name of the selected agent. Must match a key in
                    AGENT_REGISTRY exactly (e.g. "ticket_agent").

        reasoning:  The router's explanation for this choice.
                    Stored in state for observability and evaluation —
                    routing accuracy can be measured independently of
                    execution accuracy.

    model_config:
        extra="forbid" emits additionalProperties: false in the JSON
        schema, required by OpenAI's structured output API.
    """

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    reasoning:  str