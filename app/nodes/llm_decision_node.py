"""
app/nodes/llm_decision_node.py

Purpose:
--------
Ask the LLM what action should happen next and store its structured
decision in AgentState. This node decides; it does not execute.

Responsibilities:
-----------------
- Read state.message.
- Call the LLM using structured output (Pydantic model parsing).
- Write state.tool_decision.
- Return updated state.

This module DOES NOT:
---------------------
- Execute any tool (tool_executor_node's responsibility).
- Write state.ticket_id, state.tool_used, or state.response.
- Own the system prompt (app/prompts/tool_decision_prompt.py owns it).
- Construct the OpenAI client (app/llm/openai_client.py owns it).
- Build tool arguments (tool_executor_node reads state directly —
  Design B: LLM owns tool_name + reasoning; executor owns arguments).

Architecture:
-------------
    AgentState
          ↓
    llm_decision_node       ← this file (decision only)
          ↓
    state.tool_decision
          ↓
    tool_executor_node      ← future node (execution only)
          ↓
    Updated AgentState

Why structured output instead of json.loads():
-----------------------------------------------
Previous version used:
    raw = llm.call()
    parsed = json.loads(raw)
    decision = ToolDecision(**parsed)

This chain has three failure points: LLM format, JSON parsing, schema fit.

Current version uses:
    client.beta.chat.completions.parse(response_format=ToolDecision)

The SDK validates the response against the Pydantic model directly.
One step, one failure mode, no manual JSON handling.

Why Design B for arguments:
----------------------------
customer_id and message already live in state — the caller put them there.
Asking the LLM to re-state them wastes tokens and creates a failure surface
for values the model didn't derive.
The executor reads state.customer_id and state.message directly.
Design A (LLM fills arguments) applies when tools need values the LLM
extracts or synthesizes that don't already exist in state.
"""

import logging

from app.config.settings import settings
from app.llm.openai_client import get_openai_client
from app.prompts.tool_decision_prompt import TOOL_DECISION_SYSTEM_PROMPT
from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import NO_TOOL, ToolDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node: llm_decision_node
#
# LangGraph node contract: (state: AgentState) -> AgentState
#
# Reads:  state.message
# Writes: state.tool_decision
#
# Does NOT write: state.tool_used, state.ticket_id, state.response
# ---------------------------------------------------------------------------

def llm_decision_node(state: AgentState) -> AgentState:
    """
    Ask the LLM what action to take and store its decision in state.

    Uses client.beta.chat.completions.parse() to get a ToolDecision
    directly from the LLM — no manual JSON parsing, no format guessing.
    The SDK validates the response against the ToolDecision Pydantic model.

    Fallback behaviour on failure:
        Returns a no_tool ToolDecision and logs the error.
        Failing loudly (raising) would crash the graph for what is often
        a transient API issue or recoverable prompt failure.
        The executor sees is_no_tool() == True and skips execution.

        Note: silent no_tool on a real customer issue (e.g., billing error)
        is safe but not ideal. A future improvement is to set
        state.needs_human = True on parse failure so a human agent
        is notified rather than the customer receiving no response.

    Args:
        state: Current AgentState. Reads message.

    Returns:
        Updated AgentState with tool_decision populated.
    """

    logger.info(
        "llm_decision_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id
        },
    )

    try:
        client = get_openai_client()

        # client.beta.chat.completions.parse() asks the LLM to return
        # a response that conforms to the ToolDecision Pydantic schema.
        # The SDK handles serialization and validation internally.
        # No json.loads(), no ToolDecision(**parsed) — one step.
        completion = client.beta.chat.completions.parse(
            model=settings.openai_model,
            temperature=0,      # Deterministic: tool selection is not creative.
            max_tokens=200,     # ToolDecision (tool_name + reasoning) is small.
                                # Tighter cap than before since arguments are gone.
            messages=[
                {"role": "system", "content": TOOL_DECISION_SYSTEM_PROMPT},
                {"role": "user",   "content": state.message},
            ],
            response_format=ToolDecision,
        )

        tool_decision = completion.choices[0].message.parsed

        # parsed can be None if the model returned an empty or refusal response.
        if tool_decision is None:
            raise ValueError("LLM returned no parsed content (possible refusal).")

    except Exception as e:
        # Single broad catch — all failure modes (network, API, parse, refusal)
        # get the same fallback treatment: log, continue, skip execution.
        # Specific exception types are logged via repr(e) for observability.
        logger.error(
            "llm_decision_node failed: %s — falling back to no_tool",
            repr(e),
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )
        tool_decision = ToolDecision(
            tool_name=NO_TOOL,
            reasoning=f"Fallback: decision node failed ({type(e).__name__}).",
        )

    state.tool_decision = tool_decision

    logger.info(
        "llm_decision_node completed",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_decision.tool_name,
            "reasoning": tool_decision.reasoning,
        },
    )

    return state