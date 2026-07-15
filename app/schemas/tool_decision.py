"""
app/schemas/tool_decision.py

Purpose:
--------
Represent an action decision made by the LLM.

Responsibilities:
-----------------
- Capture which tool the LLM selected.
- Capture the LLM's reasoning for that selection (for observability/eval).

This module DOES NOT:
---------------------
- Execute tools.
- Call the LLM.
- Modify AgentState.
- Perform business logic or validation beyond schema constraints.

Architecture context:
---------------------
    AgentState   = everything known so far (full pipeline context)
    ToolDecision = what action should happen next (an intent to act)

Why `arguments` was removed:
------------------------------
Design B is in effect: the LLM owns tool_name and reasoning only.
The executor builds arguments from AgentState directly, since
customer_id and message already exist in state — the LLM did not
derive them and copying them into ToolDecision wastes tokens.

Why `arguments` is NOT a field here (OpenAI structured output constraint):
---------------------------------------------------------------------------
OpenAI's structured output API requires every object in the schema to have
`additionalProperties: false`. Pydantic emits this automatically on the
model itself via `extra="forbid"`, but `dict[str, Any]` generates an
open-ended object schema that cannot satisfy this constraint regardless
of the parent model's config — OpenAI rejects it with a 400 error.

When Design A is needed (LLM-derived arguments like order_id, reason):
    Define a typed Pydantic model for each tool's arguments instead:

        class CreateTicketArguments(BaseModel):
            model_config = ConfigDict(extra="forbid")
            customer_id: str
            issue: str

        class ToolDecision(BaseModel):
            ...
            arguments: CreateTicketArguments | None = None

    Typed nested models produce schemas OpenAI accepts. Open dicts do not.
"""

from pydantic import BaseModel, ConfigDict

NO_TOOL = "no_tool"


class ToolDecision(BaseModel):
    """
    An action decision produced by the LLM node.

    Fields:
        tool_name:  Name of the tool to execute, or NO_TOOL ("no_tool")
                    if the LLM determines no action is needed.

        reasoning:  The LLM's explanation for this decision.
                    Kept in the schema because evaluation systems and
                    observability tools can inspect it directly without
                    scraping logs.

    model_config:
        extra="forbid" causes Pydantic to emit `additionalProperties: false`
        in the JSON schema, which is required by OpenAI's structured output API.
    """

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    reasoning: str

    def is_no_tool(self) -> bool:
        """Return True if the LLM decided no tool should be called."""
        return self.tool_name == NO_TOOL