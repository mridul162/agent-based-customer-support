"""
app/nodes/memory_writer_node.py

Purpose:
--------
Persist the current turn (user message + agent response) to
ConversationService after the specialist agent has finished.

Responsibilities:
-----------------
- Read state.customer_id, state.message, state.response.
- Append this turn to ConversationService.
- Return state unchanged (writing is a side effect, not a state mutation).

This module DOES NOT:
---------------------
- Load history (memory_loader_node's responsibility).
- Modify state.response or state.conversation_history in state
  (the in-state history is the snapshot loaded at the start of this
  request; the service is the persistent store).
- Make LLM calls or execute tools.

Architecture position:
----------------------
    agent_dispatch_node   → specialist agent runs, response generated
      ↓
    memory_writer_node    → persists this turn to ConversationService  ← this file
      ↓
    END

Why not update state.conversation_history here?
-----------------------------------------------
The in-state history is a snapshot loaded at the start of the request.
It represents "what the agent knew when processing began."
The writer's job is persistence, not state mutation.
The next request's memory_loader_node will load the updated history.
This keeps the read (loader) and write (writer) responsibilities clean.
"""

import logging

from app.schemas.agent_state import AgentState
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


def memory_writer_node(state: AgentState) -> AgentState:
    """
    Persist the current request/response turn to conversation history.

    If state.response is None (e.g., pipeline failed before response_node),
    writes a fallback message so the user turn is still recorded.
    An orphaned user message with no assistant response would corrupt
    the conversation history structure.

    Args:
        state: Current AgentState. Reads customer_id, message, response.

    Returns:
        State unchanged — writing is a side effect only.
    """

    response_text = state.response or (
        "I'm sorry, I was unable to process your request. "
        "Please try again or contact support."
    )

    conversation_service.append_turn(
        customer_id=state.customer_id,
        user_message=state.message,
        assistant_response=response_text,
    )

    logger.info(
        "memory_writer_node: persisted turn for customer '%s'. "
        "History now has %d messages.",
        state.customer_id,
        len(conversation_service.get_history(state.customer_id)),
    )

    return state