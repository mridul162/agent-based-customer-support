"""
app/schemas/tool_decision.py

Purpose:
--------
Represent an action decision made by the LLM.

Responsibilities:
-----------------
- Capture which tool the LLM selected.
- Capture the LLM's reasoning for that selection (for observability/eval).
- Capture the arguments the tool requires to execute.

This module DOES NOT:
---------------------
- Execute tools.
- Call the LLM.
- Modify AgentState.
- Perform business logic or validation beyond schema constraints.

Architecture context:
---------------------
There are two distinct concepts this schema separates:

    AgentState      = everything known so far (full pipeline context)
    ToolDecision    = what action should happen next (an intent to act)

These are different responsibilities.
State answers:  "What do we know?"
ToolDecision answers: "What should we do, and how?"

Why `arguments` belongs here (not just in state):
    Today's graph nodes receive state.customer_id and state.message,
    which is sufficient for create_ticket_tool().

    Future tools will require parameters that don't naturally live in state:

        get_order_status_tool(order_id)
        refund_tool(order_id, reason)
        escalate_tool(ticket_id, escalation_reason)

    Putting all possible tool parameters onto AgentState creates a
    massive shared state object that's hard to maintain and understand.

    ToolDecision carries exactly the arguments needed for one tool call —
    no more, no less. The executor receives a ToolDecision and knows
    everything it needs without inspecting state.

LLM → ToolDecision → Tool Executor flow (upcoming milestone):

    LLM Node
        ↓
    ToolDecision(
        tool_name="create_ticket_tool",
        reasoning="Customer is requesting a refund.",
        arguments={"customer_id": "C001", "issue": "I was charged twice."}
    )
        ↓
    Tool Executor Node  ← reads tool_name + arguments, knows nothing else
        ↓
    Tool
        ↓
    Updated State
"""

from typing import Any

from pydantic import BaseModel, Field


# Sentinel value used when the LLM determines no tool should be called.
# Using a constant prevents "no_tool" from being scattered as a magic
# string across the codebase. Any executor checking for no-op uses this.
NO_TOOL = "no_tool"


class ToolDecision(BaseModel):
    """
    An action decision produced by the LLM node.

    Fields:
        tool_name:  Name of the tool to execute, or NO_TOOL ("no_tool")
                    if the LLM determines no action is needed.

        reasoning:  The LLM's explanation for this decision.
                    Kept in the schema (not just logs) because:
                    - It flows through AgentState for observability.
                    - Evaluation systems can inspect it directly.
                    - It makes agent behavior auditable without log scraping.

        arguments:  Key-value pairs the tool needs to execute.
                    Today (Design B): left empty — the tool executor reads
                    customer_id and message directly from AgentState, since
                    the LLM did not derive those values.
                    Future (Design A): populated by the LLM when tools need
                    values it extracted or derived — e.g., order_id from
                    "my order 12345 never arrived", or reason synthesized
                    from a long complaint. At that point, the LLM is
                    contributing new information that doesn't exist in state.
    """

    tool_name: str
    reasoning: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    def is_no_tool(self) -> bool:
        """
        Return True if the LLM decided no tool should be called.

        Prefer this over checking tool_name == "no_tool" directly,
        so the sentinel comparison is centralised here.
        """
        return self.tool_name == NO_TOOL