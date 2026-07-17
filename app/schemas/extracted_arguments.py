"""
app/schemas/extracted_arguments.py

Purpose:
--------
Store structured information extracted from a customer's natural language
message by the argument extraction node.

Responsibilities:
-----------------
- Hold key-value pairs extracted from language (ticket_id, order_id, reason, etc.).
- Provide a single, isolated home for extraction output in AgentState.
- Remain tool-agnostic — it stores what was found, not how it will be used.

This module DOES NOT:
---------------------
- Extract information from messages (argument_extraction_node's responsibility).
- Know which tool will consume the extracted values.
- Validate that extracted values satisfy any particular tool's requirements.
- Perform business logic or modify AgentState directly.

Architecture context:
---------------------
The agent pipeline is evolving from:

    Message → Decision → Execution

to:

    Message → Decision → Extraction → Execution

The extraction node needs a dedicated place to store its output that is:

    1. Separate from workflow state (AgentState owns workflow concepts;
       this schema owns extracted language concepts — different responsibilities).

    2. Tool-agnostic (the extraction node finds values; it doesn't know
       how the executor will use them).

    3. Stable as tools grow (a flat dict avoids adding a new AgentState
       field for every new extractable entity — ticket_id, order_id,
       reason, product_name, tracking_number would all pollute AgentState).

Why dict[str, Any] and not typed fields:
-----------------------------------------
A typed approach would look like:

    class ExtractedArguments(BaseModel):
        ticket_id: str | None = None
        order_id: str | None = None
        reason: str | None = None

This forces a schema change every time a new tool needs a new entity.
We are building an extraction framework, not a ticket extraction framework.

A dict-based approach:

    ExtractedArguments(values={"ticket_id": "TICKET-123"})
    ExtractedArguments(values={"order_id": "ORD-999", "reason": "damaged"})

lets the extraction node store whatever it finds, and the executor reads
what it needs by key. The schema stays stable as tools multiply.

Note on OpenAI structured output:
-----------------------------------
ExtractedArguments is NOT used as a response_format for LLM calls.
It is only used internally to store extraction output in AgentState.
Therefore dict[str, Any] is acceptable here — the OpenAI additionalProperties
constraint only applies to schemas passed as response_format.

Ownership boundary:
-------------------
    Extraction node  → writes ExtractedArguments.values
    Tool executor    → reads ExtractedArguments.values via .get()
    Neither          → knows about the other's internal logic

Example state after extraction:

    "What's the status of ticket TICKET-123?"
    → state.extracted_arguments.values = {"ticket_id": "TICKET-123"}

    "Refund order ORD-999 because it arrived damaged."
    → state.extracted_arguments.values = {
          "order_id": "ORD-999",
          "reason": "damaged item"
      }

The extraction node doesn't know how the tool uses these values.
The executor doesn't know how these values were extracted.
That's the correct separation.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExtractedArguments(BaseModel):
    """
    Tool-agnostic container for values extracted from natural language.

    Fields:
        values:     Dict mapping entity names to extracted values.
                    Keys are strings (entity names like "ticket_id", "order_id").
                    Values are Any to support strings, numbers, and future types.
                    Defaults to empty dict — extraction may find nothing,
                    which is a valid and expected result for some messages.

    Usage:
        # Extraction node writes:
        state.extracted_arguments = ExtractedArguments(
            values={"ticket_id": "TICKET-123"}
        )

        # Executor reads:
        ticket_id = state.extracted_arguments.get("ticket_id")
    """

    values: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs of entities extracted from the customer's message.",
    )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Convenience accessor — mirrors dict.get() so callers don't need
        to access .values directly for simple lookups.

        Args:
            key:     Entity name to look up (e.g., "ticket_id").
            default: Value to return if key is not present.

        Returns:
            Extracted value if found, default otherwise.
        """
        return self.values.get(key, default)

    def has(self, key: str) -> bool:
        """
        Return True if the given entity was extracted.

        Preferred over `key in state.extracted_arguments.values`
        for readability at call sites.
        """
        return key in self.values