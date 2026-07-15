"""
app/schemas/agent_state.py

Purpose:
--------
Represent the complete state of a single agent execution turn.

Responsibilities:
-----------------
- Store customer input (customer_id, message).
- Store detected intent.
- Store the LLM's tool decision (what action to take, why, with what args).
- Store tool execution results (tool_used, ticket_id).
- Store the final response.
- Store the escalation flag.

This module DOES NOT:
---------------------
- Execute agent logic.
- Call tools or LLMs.
- Manage memory across turns.
- Persist state to a database.

Architecture Philosophy:
------------------------
State is the shared language between all workflow steps (nodes).
Each node reads what it needs from state, writes what it produces,
and returns the updated state.

    Node A (llm_decision_node)
        reads:  state.message
        writes: state.tool_decision

    Node B (tool_executor_node)
        reads:  state.tool_decision
        writes: state.tool_used, state.ticket_id, state.response

No node needs to know what another node does internally.
They communicate only through this shared state object.

Field additions history:
------------------------
- Milestone 1: customer_id, message, intent, tool_used, ticket_id,
               response, needs_human
- Milestone 4: tool_decision  ← added to support LLM decision node.
               The LLM node writes a ToolDecision here.
               The tool executor node reads it to perform execution.
               Keeping decision and execution results as separate fields
               makes each node's contract explicit and auditable.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.agent import Intent
from app.schemas.tool_decision import ToolDecision


class AgentState(BaseModel):
    """
    Shared state object passed through every node in the agent graph.

    Fields are grouped by the stage that writes them:

    Input (set by handle_message / graph entry):
        customer_id:   The customer's unique identifier.
        message:       The raw customer message.

    Intent Detection (written by detect_intent_node):
        intent:        Classified Intent enum value. None until detected.

    LLM Decision (written by llm_decision_node):
        tool_decision: The structured action decision from the LLM.
                       Contains tool_name, reasoning, and arguments.
                       None until the LLM node runs.
                       Kept separate from execution results so decision
                       and execution can be observed and evaluated independently.

    Tool Execution (written by tool_executor_node or handler nodes):
        tool_used:     Name of the tool that was actually called.
        ticket_id:     ID of the created ticket, if any.
        response:      Final response text to return to the customer.

    Control (set by any node that determines escalation is needed):
        needs_human:   True if the agent cannot handle this and a human
                       agent should take over.
    """

    # -- Input --
    customer_id: str
    message: str

    # -- Intent Detection --
    intent: Intent | None = None

    # -- LLM Decision --
    # Stores the full ToolDecision (tool_name + reasoning + arguments).
    # Written by llm_decision_node; read by tool_executor_node.
    # Separate from tool_used so we can distinguish:
    #   "what the LLM decided"  vs  "what was actually executed."
    # This separation is important for evaluation: if execution fails,
    # we still have the LLM's original decision for debugging.
    tool_decision: ToolDecision | None = None

    # -- Tool Execution --
    # tool_result preserves the raw object returned by the executed tool.
    # This is the 'observation' in the Reason → Act → Observe → Respond loop.
    #
    # Why Any instead of a specific type?
    #     Different tools return different types (TicketResponse, OrderStatus, etc.).
    #     The executor stores whatever the tool returns; downstream nodes
    #     cast to the type they need. Forcing a union type here would couple
    #     AgentState to every tool's return type — wrong ownership.
    #
    # Why preserve the full object instead of flattening fields?
    #     Flattening (state.ticket_id = ticket.ticket_id) discards information.
    #     Future nodes may need ticket.status, ticket.customer_id, ticket.issue.
    #     The executor cannot predict what later nodes will need, so it stores
    #     the full result and lets each consumer extract what it needs.
    tool_result: Any | None = None
    tool_used: str | None = None
    ticket_id: str | None = None
    response: str | None = None

    # -- Control --
    needs_human: bool = False