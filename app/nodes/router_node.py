"""
app/nodes/router_node.py

Purpose:
--------
Ask the LLM which specialist agent should handle the customer's request
and write the structured routing decision to AgentState.

Responsibilities:
-----------------
- Read state.message.
- Call the LLM with the router prompt.
- Parse the response into a RoutingDecision.
- Write state.routing_decision.
- Return updated state.

This module DOES NOT:
---------------------
- Dispatch to agents (agent_dispatch_node's responsibility).
- Execute tools or generate customer responses.
- Read state.tool_decision (routing is independent of tool selection).
- Know about specific agent implementations.

Architecture:
-------------
    START
      ↓
    router_node           → reads message, writes routing_decision
      ↓
    agent_dispatch_node   → reads routing_decision, invokes agent graph
      ↓
    END

Why routing is a separate node from tool decision:
---------------------------------------------------
The router answers: "Who handles this?"
The LLM decision node answers: "What tool does the handler use?"

These are different levels of abstraction. The router operates above
the agent — it selects which workflow runs. The LLM decision node
operates inside an agent — it selects which tool the agent calls.
Merging them would couple routing logic to tool knowledge.

Fallback behaviour:
-------------------
On any failure (parse error, API error), defaults to "ticket_agent".
ticket_agent is the most general handler and the safest default —
it can create a ticket for any issue, so no customer request is lost.
"""

import logging

from app.config.settings import settings
from app.llm.openai_client import get_openai_client
from app.prompts.router_prompt import ROUTER_SYSTEM_PROMPT
from app.schemas.agent_state import AgentState
from app.schemas.routing_decision import RoutingDecision

logger = logging.getLogger(__name__)

# Fallback agent when the router fails to produce a valid decision.
# ticket_agent is chosen because it handles the broadest range of issues.
_FALLBACK_AGENT = "ticket_agent"


def router_node(state: AgentState) -> AgentState:
    """
    Route the customer's message to the appropriate specialist agent.

    Uses structured output (response_format=RoutingDecision) to get a
    typed decision directly — same pattern as llm_decision_node.

    Args:
        state: Current AgentState. Reads message.

    Returns:
        Updated AgentState with routing_decision populated.
    """

    logger.info(
        "router_node started",
        extra={"customer_id": state.customer_id},
    )

    try:
        client = get_openai_client()

        completion = client.beta.chat.completions.parse(
            model=settings.openai_model,
            temperature=0,      # Routing is deterministic — same message, same agent.
            max_tokens=150,     # agent_name + reasoning is very short.
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user",   "content": state.message},
            ],
            response_format=RoutingDecision,
        )

        routing_decision = completion.choices[0].message.parsed

        if routing_decision is None:
            raise ValueError("Router returned no parsed content.")

    except Exception as e:
        logger.error(
            "router_node failed: %s — falling back to '%s'.",
            repr(e), _FALLBACK_AGENT,
            extra={"customer_id": state.customer_id},
        )
        routing_decision = RoutingDecision(
            agent_name=_FALLBACK_AGENT,
            reasoning=f"Fallback: router failed ({type(e).__name__}).",
        )

    state.routing_decision = routing_decision

    logger.info(
        "router_node completed",
        extra={
            "agent_name": routing_decision.agent_name,
            "reasoning":  routing_decision.reasoning,
        },
    )

    return state