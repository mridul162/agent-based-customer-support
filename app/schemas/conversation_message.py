"""
app/schemas/conversation_message.py

Purpose:
--------
Define a single turn in a customer conversation.

Responsibilities:
-----------------
- Represent one message from either the user or the assistant.
- Provide a typed, serializable unit of conversation history.

This module DOES NOT:
---------------------
- Store or retrieve messages (ConversationService owns that).
- Know about AgentState or the graph.
- Perform any business logic.

Architecture context:
---------------------
ConversationMessage is the unit stored in:
    - ConversationService (in-memory, later PostgreSQL)
    - AgentState.conversation_history (available to all nodes)

The history list flows through the graph so any node can read
prior context without calling the service directly.
"""

from typing import Literal

from pydantic import BaseModel


class ConversationMessage(BaseModel):
    """
    One turn in a customer conversation.

    Fields:
        role:    "user" for customer messages, "assistant" for agent responses.
        content: The raw text of the message or response.
    """

    role:    Literal["user", "assistant"]
    content: str