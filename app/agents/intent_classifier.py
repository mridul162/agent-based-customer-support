"""
app/agents/intent_classifier.py

Purpose:
--------
Single source of truth for customer intent detection.

Responsibilities:
-----------------
- Define intent keyword sets.
- Classify a customer message into an Intent enum value.

This module DOES NOT:
---------------------
- Call tools or services.
- Modify AgentState directly.
- Know about LangGraph, SupportAgent, or any orchestration layer.
- Handle routing or execution flow.

Why this file exists:
---------------------
Intent detection logic was duplicated in two places:
    1. SupportAgent._detect_intent()       (Milestone 2)
    2. detect_intent_node() in support_graph.py  (Milestone 3)

When logic exists in two places, one becomes wrong eventually.
This module is the single owner of that logic.

Both SupportAgent and detect_intent_node() now delegate here:

    SupportAgent._detect_intent(state)
          ↓
    IntentClassifier.classify(message)

    detect_intent_node(state)
          ↓
    IntentClassifier.classify(message)

If keyword sets need updating, this is the only file to change.
"""

from app.schemas.agent import Intent


class IntentClassifier:
    """
    Rule-based intent classifier.

    Classifies a raw customer message into one of the supported Intent
    values using keyword matching with a defined priority order.

    Why a class and not a module-level function?
        - The keyword sets are logically grouped with the classification logic.
        - The class can later accept configuration (e.g., custom keyword sets
          injected at construction time for testing or tenant-specific rules).
        - When this is replaced by LLM-based classification, the class
          interface (classify(message) -> Intent) stays the same —
          callers don't change.

    Priority order (evaluated top to bottom):
        1. Refund   — financial impact, highest priority.
        2. Delivery — late/missing shipment context.
        3. Order    — wrong/damaged item issues.
        4. General  — fallback for anything unrecognised.
    """

    # ------------------------------------------------------------------
    # Keyword Sets
    #
    # Defined at class level so they can be inspected and tested
    # independently of the classify() method.
    #
    # "delivered" is intentionally absent from _DELIVERY_KEYWORDS.
    # "The wrong item was delivered" is ORDER_ISSUE, not DELIVERY_ISSUE.
    # Delivery keywords require an unambiguous missing/late shipment signal.
    # ------------------------------------------------------------------

    _REFUND_KEYWORDS: frozenset[str] = frozenset({
        "refund", "charged", "overcharged", "money back", "reimburs",
    })

    _DELIVERY_KEYWORDS: frozenset[str] = frozenset({
        "never arrived", "not arrived", "not delivered",
        "missing package", "lost package", "where is my package",
        "shipping delay", "not received", "delivery delay",
        "late delivery", "shipment",
    })

    _ORDER_KEYWORDS: frozenset[str] = frozenset({
        "order", "purchase", "bought", "item", "product",
        "wrong", "incorrect", "damaged", "broken",
    })

    def classify(self, message: str) -> Intent:
        """
        Classify a customer message into an Intent.

        Args:
            message: Raw customer message string.

        Returns:
            Intent enum value. Never raises — unknown messages
            fall back to GENERAL_INQUIRY.
        """

        lowered = message.lower()

        if any(kw in lowered for kw in self._REFUND_KEYWORDS):
            return Intent.REFUND_REQUEST

        if any(kw in lowered for kw in self._DELIVERY_KEYWORDS):
            return Intent.DELIVERY_ISSUE

        if any(kw in lowered for kw in self._ORDER_KEYWORDS):
            return Intent.ORDER_ISSUE

        return Intent.GENERAL_INQUIRY


# ---------------------------------------------------------------------------
# Module-level singleton.
#
# Both SupportAgent and detect_intent_node import this instance directly.
# No need to construct IntentClassifier() at every call site.
# When dependency injection is introduced later, this singleton is replaced
# by an injected instance — callers don't change.
# ---------------------------------------------------------------------------

classifier = IntentClassifier()