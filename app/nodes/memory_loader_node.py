"""
app/nodes/memory_loader_node.py

Purpose:
--------
Load the customer's conversation history from ConversationService
into AgentState before routing begins.

Responsibilities:
-----------------
- Read state.customer_id.
- Fetch conversation history from ConversationService.
- Write state.conversation_history.
- Return updated state.

This module DOES NOT:
---------------------
- Write new messages to history (memory_writer_node's responsibility).
- Make LLM calls or execute tools.
- Generate responses.
- Know about routing or specialist agents.

Architecture position:
----------------------
    START
      ↓
    memory_loader_node    → enriches state with prior context   ← this file
      ↓
    router_node           → routes with full context available
      ↓
    agent_dispatch_node
      ↓
    memory_writer_node    → persists this turn's messages

Why load before routing?
------------------------
The router may use conversation context to make better routing decisions.
Specialist agents (especially extraction) can use prior turns to recover
entities like ticket_id when the current message doesn't include them.
Loading once at the start makes context universally available without
any node needing to call the service directly.
"""

import logging

from app.schemas.agent_state import AgentState
from app.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


def memory_loader_node(state: AgentState) -> AgentState:
    """
    Load conversation history for the current customer into state.

    Args:
        state: Current AgentState. Reads customer_id.

    Returns:
        Updated AgentState with conversation_history populated.
    """

    history = conversation_service.get_history(state.customer_id)

    state.conversation_history = history

    logger.info(
        "memory_loader_node: loaded %d messages for customer '%s'.",
        len(history),
        state.customer_id,
    )

    return state