"""
app/nodes/escalation_detection_node.py

Purpose:
--------
Detect messages that require immediate human intervention before
routing to any specialist agent.

This node runs before the router so high-risk messages bypass the
standard agent pipeline entirely — the router never sees them.

Responsibilities:
-----------------
- Read state.message.
- Check for escalation keywords using rule-based matching.
- If triggered: set state.needs_human=True, set state.escalation_reason,
  determine the appropriate queue.
- Return updated state.

This node DOES NOT:
-------------------
- Create escalations in the database (escalation_agent owns that).
- Generate customer responses.
- Call the LLM.
- Know about ticket tools or the ticket agent.

Why rule-based first?
---------------------
Same reasoning applied to intent detection in Milestone 1.
Legal threats, safety concerns, and fraud allegations have clear
keyword signals. Deterministic detection is faster, cheaper, and
more auditable than LLM-based detection for high-stakes routing.
LLM-based refinement is a future improvement.

Architecture position:
----------------------
    memory_loader_node
          ↓
    escalation_detection_node   ← this file (pre-routing safety gate)
          ↓
    router_node                 (skipped if needs_human=True)
          ↓
    agent_dispatch_node         → escalation_agent if needs_human=True
"""

import logging
import re

from app.schemas.agent_state import AgentState
from app.schemas.escalation import EscalationQueue

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Escalation Signal Registry
#
# Maps EscalationQueue → list of keyword/phrase patterns.
# More specific queues are checked first (legal before general).
# ---------------------------------------------------------------------------

_LEGAL_SIGNALS: frozenset[str] = frozenset({
    "lawsuit", "attorney", "lawyer", "legal action", "sue",
    "court", "litigation", "solicitor", "legal proceedings",
})

_SAFETY_SIGNALS: frozenset[str] = frozenset({
    "dangerous", "injured", "injury", "police", "emergency",
    "unsafe", "harm", "hurt", "accident",
})

_FRAUD_SIGNALS: frozenset[str] = frozenset({
    "fraud", "scam", "stolen", "identity theft", "unauthorized charge",
    "chargeback", "dispute charge",
})

_GENERAL_ESCALATION_SIGNALS: frozenset[str] = frozenset({
    "speak to a human", "speak to a person", "speak to a manager",
    "talk to a human", "talk to a person", "talk to a manager",
    "real person", "human agent", "escalate",
})


def _detect_escalation(message: str) -> tuple[bool, str, EscalationQueue]:
    """
    Check a message for escalation signals.

    Returns:
        (escalate, reason, queue) — escalate=True if signal found.
        reason is the matched signal phrase for audit/logging.
        queue is the appropriate routing destination.
    """
    lowered = message.lower()

    # Check in priority order: legal > safety > fraud > general
    checks: list[tuple[frozenset[str], EscalationQueue, str]] = [
        (_LEGAL_SIGNALS,               EscalationQueue.LEGAL,   "legal threat"),
        (_SAFETY_SIGNALS,              EscalationQueue.SAFETY,  "safety concern"),
        (_FRAUD_SIGNALS,               EscalationQueue.BILLING, "fraud/dispute"),
        (_GENERAL_ESCALATION_SIGNALS,  EscalationQueue.GENERAL, "human requested"),
    ]

    for signals, queue, category in checks:
        for signal in signals:
            if signal in lowered:
                return True, f"{category}: '{signal}'", queue

    return False, "", EscalationQueue.GENERAL


def escalation_detection_node(state: AgentState) -> AgentState:
    """
    Pre-routing safety gate: detect messages requiring human intervention.

    If an escalation signal is detected:
        state.needs_human = True
        state.escalation_reason is set (stored for escalation_agent)
        state.escalation_queue  is set (stored for escalation_agent)

    The router_graph checks state.needs_human after this node runs
    and routes to escalation_agent instead of calling router_node.

    Args:
        state: Current AgentState. Reads message.

    Returns:
        Updated AgentState. May set needs_human=True.
    """
    escalate, reason, queue = _detect_escalation(state.message)

    if escalate:
        state.needs_human       = True
        state.escalation_reason = reason
        state.escalation_queue  = queue.value

        logger.info(
            "escalation_detection_node: escalation signal detected.",
            extra={
                "request_id":  state.request_id,
                "customer_id": state.customer_id,
                "reason":      reason,
                "queue":       queue.value,
            },
        )
    else:
        logger.debug(
            "escalation_detection_node: no signal — passing to router.",
            extra={
                "request_id":  state.request_id,
                "customer_id": state.customer_id,
            },
        )

    return state