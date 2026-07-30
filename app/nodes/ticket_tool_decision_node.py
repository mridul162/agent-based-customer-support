"""
LLM decision node for the ticket specialist agent.
"""

import logging

from app.config.settings import settings
from app.llm.llm_service import LLMService
from app.prompts.ticket_tool_decision_prompt import (
    TICKET_TOOL_DECISION_SYSTEM_PROMPT,
)
from app.schemas.agent_state import AgentState
from app.schemas.tool_decision import NO_TOOL, ToolDecision

logger = logging.getLogger(__name__)


def ticket_tool_decision_node(state: AgentState) -> AgentState:
    """
    Select a ticket tool using the LLM and store it in state.tool_decision.
    """

    logger.info(
        "ticket_tool_decision_node started",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
        },
    )

    try:
        completion = LLMService.parse_chat_completion(
            model=settings.openai_model,
            temperature=0,
            max_tokens=200,
            messages=[
                {"role": "system", "content": TICKET_TOOL_DECISION_SYSTEM_PROMPT},
                {"role": "user", "content": state.message},
            ],
            response_format=ToolDecision,
            execution_trace=state.execution_trace,
            node_name="ticket_tool_decision_node",
        )

        tool_decision = completion.choices[0].message.parsed

        if tool_decision is None:
            raise ValueError("LLM returned no parsed ticket tool decision.")

    except Exception as exc:
        logger.error(
            "ticket_tool_decision_node failed: %s - falling back to no_tool",
            repr(exc),
            extra={
                "request_id": state.request_id,
                "customer_id": state.customer_id,
            },
        )
        tool_decision = ToolDecision(
            tool_name=NO_TOOL,
            reasoning=f"Fallback: ticket decision failed ({type(exc).__name__}).",
        )

    state.tool_decision = tool_decision

    logger.info(
        "ticket_tool_decision_node completed",
        extra={
            "request_id": state.request_id,
            "customer_id": state.customer_id,
            "tool_name": tool_decision.tool_name,
        },
    )

    return state
