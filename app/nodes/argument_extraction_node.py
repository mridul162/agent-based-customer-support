"""
app/nodes/argument_extraction_node.py

Purpose:
--------
Extract structured entities from the customer's natural language message
and write them to AgentState as extracted_arguments.

This is a state enrichment node — its sole job is to enrich state with
structured information found in the message, so downstream nodes (the
executor) can consume it without performing any language understanding.

Responsibilities:
-----------------
- Read state.message.
- Extract known entity types using pattern matching.
- Write state.extracted_arguments.
- Return updated state.

This module DOES NOT:
---------------------
- Read state.tool_decision (extraction is message-driven, not tool-driven).
- Know which tool will consume the extracted values.
- Execute tools or modify business data.
- Generate customer-facing responses.
- Validate that extracted values satisfy any tool's requirements.

Architecture position:
----------------------
    llm_decision_node       → Reason
          ↓
    argument_extraction_node → Extract   ← this file
          ↓
    tool_executor_node      → Act
          ↓
    response_node           → Respond

Why message-driven (not tool-driven):
--------------------------------------
The extraction node answers: "What information exists in this message?"
The executor answers:        "What information does this tool require?"

If extraction were tool-driven (reading state.tool_decision to know
what to extract), it would become coupled to tool signatures. Changing
a tool's required arguments would then require changing extraction logic —
a dependency direction violation.

Message-driven extraction is also reusable: extracted_arguments is
populated once and can be consumed by multiple downstream agents or nodes
without re-running extraction.

Extraction strategy — Regex for Milestone 5:
---------------------------------------------
Ticket IDs have a fixed, known format: TICKET- followed by alphanumerics.
This is a structured extraction problem. Using an LLM to extract a value
that a pattern can match deterministically would add:
    - Latency (extra API call per request)
    - Cost (tokens spent on a trivial match)
    - Opacity (LLM failures are harder to trace than pattern failures)

Regex failures are immediate, reproducible, and testable without an API key.
When extraction fails, the cause is in the pattern — deterministic and fixable.

Upgrade path to hybrid:
    When unstructured entities arrive (reason, product_name, free-text),
    those get LLM extraction added alongside the regex layer.
    This node's interface (read message → write extracted_arguments) never
    changes — only the internal extraction strategies grow.
"""

import logging
import re

from app.schemas.agent_state import AgentState
from app.schemas.conversation_message import ConversationMessage
from app.schemas.extracted_arguments import ExtractedArguments

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Entity Patterns
#
# Each pattern is compiled once at module level (not inside the node function)
# to avoid recompiling on every invocation.
#
# Patterns are intentionally strict:
#     TICKET-  must be followed by at least one alphanumeric character.
#     \b word boundaries prevent partial matches inside longer strings.
#
# When new entity types are added, add a new pattern here and a new
# extraction call in _extract_all(). The node function never changes.
# ---------------------------------------------------------------------------

# Matches: TICKET-123, TICKET-ABC123, TICKET-99999, TICKET-34D61027
# Case-insensitive so "ticket-123" and "TICKET-123" both match.
_TICKET_ID_PATTERN = re.compile(
    r'\bTICKET-[A-Z0-9]+\b',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Extraction Functions
#
# Each function extracts one entity type from a message string.
# Returns the extracted value or None if not found.
#
# Taking the first match is deliberate: if a customer mentions multiple
# ticket IDs, we take the first one. Ambiguous multi-entity messages are
# a future problem (they may require clarification, not silent extraction).
# ---------------------------------------------------------------------------

def _extract_ticket_id(message: str) -> str | None:
    """
    Extract the first ticket ID found in the message.

    Returns the matched string in uppercase, normalised form,
    or None if no ticket ID is present.
    """
    match = _TICKET_ID_PATTERN.search(message)
    if match:
        return match.group(0).upper()
    return None


# ---------------------------------------------------------------------------
# _extract_all
#
# Runs all extraction functions against the message and returns a dict
# of found entities. Only non-None values are included — the executor
# uses .get() with a default, so absent keys are handled cleanly.
#
# Adding a new entity:
#     1. Add a compiled pattern above.
#     2. Add an _extract_<entity>() function.
#     3. Add one line here.
#     The node function never changes.
# ---------------------------------------------------------------------------

def _extract_all(message: str) -> dict[str, str]:
    """
    Run all entity extractors against the message.

    Returns a dict containing only the entities that were found.
    Absent entities are not included (not set to None) so callers
    can distinguish "not found" from "found but empty".
    """
    extracted: dict[str, str] = {}

    ticket_id = _extract_ticket_id(message)
    if ticket_id is not None:
        extracted["ticket_id"] = ticket_id

    return extracted


# ---------------------------------------------------------------------------
# Node: argument_extraction_node
#
# LangGraph node contract: (state: AgentState) -> AgentState
#
# Reads:  state.message
# Writes: state.extracted_arguments
#
# Deliberately does NOT read: state.tool_decision
# This enforces message-driven extraction.
# ---------------------------------------------------------------------------

def _recover_ticket_id_from_history(
    history: list,
) -> str | None:
    """
    Search prior assistant messages for a ticket ID.

    Scans from most recent to oldest so the latest ticket is preferred
    when a customer has created multiple tickets in one conversation.

    Args:
        history: list[ConversationMessage] from state.conversation_history.

    Returns:
        Extracted ticket_id string or None if not found in history.
    """
    for message in reversed(history):
        if message.role == "assistant":
            match = _TICKET_ID_PATTERN.search(message.content)
            if match:
                return match.group(0).upper()
    return None


def argument_extraction_node(state: AgentState) -> AgentState:
    """
    Extract structured entities from the customer's message.

    Runs all registered extractors against state.message and writes
    the results to state.extracted_arguments.

    An empty extraction result is valid — not every message contains
    extractable entities. The executor handles missing values via
    extracted_arguments.get(key, default).

    Args:
        state: Current AgentState. Reads message only.

    Returns:
        Updated AgentState with extracted_arguments populated.
    """

    logger.info(
        "argument_extraction_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id
        },
    )

    found = _extract_all(state.message)

    # Memory fallback: if ticket_id was not found in the current message,
    # search conversation history for a prior assistant response containing one.
    # This handles "What's the status?" after "Ticket TICKET-123 created."
    if "ticket_id" not in found:
        recovered = _recover_ticket_id_from_history(state.conversation_history)
        if recovered:
            found["ticket_id"] = recovered
            logger.info(
                "argument_extraction_node: recovered ticket_id '%s' from history.",
                recovered,
                extra={
                    "request_id": state.request_id,
                    "customer_id": state.customer_id
                },
            )

    state.extracted_arguments = ExtractedArguments(values=found)

    logger.info(
        "argument_extraction_node completed",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "extracted_keys": list(found.keys()),
            "extracted_count": len(found),
        },
    )

    return state