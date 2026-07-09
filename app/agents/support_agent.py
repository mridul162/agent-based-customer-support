"""
app/agents/support_agent.py

Responsibility:
    - Receive a customer message and ID.
    - Detect the customer's intent (rule-based for Milestone 1).
    - Select and call the appropriate tool.
    - Return a structured AgentResponse.

Should NOT:
    - Call TicketService directly (must go through tools).
    - Return free-form strings (must return AgentResponse).
    - Own business rules (e.g., setting ticket status to OPEN).
    - Contain SQL, database logic, or prompt templates.

Architecture:
    Customer Message
          ↓
    SupportAgent.handle_message()
          ↓
    Intent Detection (rule-based)
          ↓
    Tool Selection + Execution
          ↓
    AgentResponse (structured)

Why rule-based intent detection first?
    Adding an LLM immediately would obscure whether failures come from
    agent design, tool design, prompt design, or model behavior.
    Rule-based logic removes that uncertainty while the architecture
    is still being established. LLM reasoning replaces this later.
"""

from typing import Callable

from app.schemas.agent import AgentResponse, Intent
from app.tools.ticket_tools import create_ticket_tool

# Type alias for handler functions.
# Every handler receives (customer_id, message, intent) and returns AgentResponse.
# Defined here so _INTENT_HANDLERS is readable at a glance.
HandlerFn = Callable[[str, str, Intent], AgentResponse]


class SupportAgent:
    """
    Rule-based customer support agent for Milestone 1.

    Detects intent from the customer's message using keyword matching,
    dispatches to a dedicated handler via _INTENT_HANDLERS, and returns
    a typed AgentResponse.

    Architectural change from first version:
        The original _route() coupled routing logic (which handler?)
        with response logic (what does each handler say?).
        This version separates them:
            - _INTENT_HANDLERS  → owns routing (intent → handler mapping)
            - _handle_*()       → each owns one intent's tool call + response
            - _route()          → a single dispatch lookup, never grows

        Adding a new intent now means:
            1. Add keywords to _detect_intent().
            2. Add a _handle_new_intent() method.
            3. Add one entry to _INTENT_HANDLERS.
        _route() and handle_message() never need to change.

    The agent interacts ONLY with tools — never with services or the
    database directly. This keeps the agent swappable (rule-based today,
    LangGraph tomorrow) without touching the layers beneath it.
    """

    # ------------------------------------------------------------------
    # Intent Detection
    # ------------------------------------------------------------------

    _REFUND_KEYWORDS   = {"refund", "charged", "overcharged", "money back", "reimburs"}

    # "delivered" is intentionally excluded from delivery keywords.
    # "The wrong item was delivered" is an ORDER_ISSUE, not a DELIVERY_ISSUE.
    # Delivery keywords now require a stronger signal: late/missing shipment context.
    # "delivered" alone is too ambiguous — it appears in order-issue messages too.
    _DELIVERY_KEYWORDS = {"never arrived", "not arrived", "not delivered",
                          "missing package", "lost package", "where is my package",
                          "shipping delay", "not received", "delivery delay",
                          "late delivery", "shipment"}

    # "wrong", "incorrect", "damaged", "broken" capture order-issue messages
    # where something was delivered but was the wrong or defective thing.
    _ORDER_KEYWORDS    = {"order", "purchase", "bought", "item", "product",
                          "wrong", "incorrect", "damaged", "broken"}

    def _detect_intent(self, message: str) -> Intent:
        """
        Detect intent via keyword matching, evaluated in priority order:
            1. Refund   — financial impact, highest priority.
            2. Delivery — physical fulfilment issues.
            3. Order    — general order/product issues.
            4. General  — fallback for anything unrecognised.
        """

        lowered = message.lower()

        if any(kw in lowered for kw in self._REFUND_KEYWORDS):
            return Intent.REFUND_REQUEST

        if any(kw in lowered for kw in self._DELIVERY_KEYWORDS):
            return Intent.DELIVERY_ISSUE

        if any(kw in lowered for kw in self._ORDER_KEYWORDS):
            return Intent.ORDER_ISSUE

        return Intent.GENERAL_INQUIRY

    # ------------------------------------------------------------------
    # Intent Handlers
    # Each handler owns exactly one intent's tool call and response text.
    # No handler knows about any other intent.
    # ------------------------------------------------------------------

    def _handle_refund_request(
        self,
        customer_id: str,
        message: str,
        intent: Intent,
    ) -> AgentResponse:
        ticket = create_ticket_tool(customer_id=customer_id, issue=message)
        return AgentResponse(
            intent=intent,
            tool_used="create_ticket_tool",
            ticket_id=ticket.ticket_id,
            response=(
                f"I've raised a refund request for you. "
                f"Your ticket ID is {ticket.ticket_id}. "
                f"Our team will review it and get back to you shortly."
            ),
        )

    def _handle_delivery_issue(
        self,
        customer_id: str,
        message: str,
        intent: Intent,
    ) -> AgentResponse:
        ticket = create_ticket_tool(customer_id=customer_id, issue=message)
        return AgentResponse(
            intent=intent,
            tool_used="create_ticket_tool",
            ticket_id=ticket.ticket_id,
            response=(
                f"I've logged a delivery issue for you. "
                f"Your ticket ID is {ticket.ticket_id}. "
                f"We'll investigate and update you as soon as possible."
            ),
        )

    def _handle_order_issue(
        self,
        customer_id: str,
        message: str,
        intent: Intent,
    ) -> AgentResponse:
        ticket = create_ticket_tool(customer_id=customer_id, issue=message)
        return AgentResponse(
            intent=intent,
            tool_used="create_ticket_tool",
            ticket_id=ticket.ticket_id,
            response=(
                f"I've created a support ticket for your order issue. "
                f"Your ticket ID is {ticket.ticket_id}. "
                f"A support specialist will follow up with you soon."
            ),
        )

    def _handle_general_inquiry(
        self,
        customer_id: str,
        message: str,
        intent: Intent,
    ) -> AgentResponse:
        # No ticket created. No tool used.
        # The agent responds directly with a clarifying question.
        return AgentResponse(
            intent=intent,
            tool_used=None,
            ticket_id=None,
            response=(
                "Thank you for reaching out. Could you provide more details "
                "about your issue so I can assist you better?"
            ),
        )

    # ------------------------------------------------------------------
    # Dispatch Table
    #
    # Maps each Intent to its handler method.
    # _route() performs a single lookup here — it never grows as new
    # intents are added. Adding a new intent = one new entry below.
    #
    # Why a property and not a class-level dict?
    # Handler methods are instance methods (self._handle_*).
    # At class definition time, self doesn't exist yet, so we can't
    # reference instance methods directly as class-level values.
    # A property resolves this cleanly without any extra machinery.
    # ------------------------------------------------------------------

    @property
    def _INTENT_HANDLERS(self) -> dict[Intent, HandlerFn]:
        return {
            Intent.REFUND_REQUEST:  self._handle_refund_request,
            Intent.DELIVERY_ISSUE:  self._handle_delivery_issue,
            Intent.ORDER_ISSUE:     self._handle_order_issue,
            Intent.GENERAL_INQUIRY: self._handle_general_inquiry,
        }

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _route(
        self,
        intent: Intent,
        customer_id: str,
        message: str,
    ) -> AgentResponse:
        """
        Dispatch to the correct handler via _INTENT_HANDLERS.

        This method never grows. Adding new intents only requires
        adding a new handler and a new entry in _INTENT_HANDLERS.

        Falls back to _handle_general_inquiry if an unmapped intent
        is somehow passed in — defensive, not speculative.
        """

        handler = self._INTENT_HANDLERS.get(intent, self._handle_general_inquiry)
        return handler(customer_id, message, intent)

    # ------------------------------------------------------------------
    # Public Interface
    # ------------------------------------------------------------------

    def handle_message(
        self,
        customer_id: str,
        message: str,
    ) -> AgentResponse:
        """
        Entry point for all customer interactions.

        Workflow:
            1. Detect intent from the message.
            2. Dispatch to the correct handler via _route().
            3. Return a structured AgentResponse.

        This is the only public method on SupportAgent.
        """

        intent = self._detect_intent(message)
        return self._route(intent, customer_id, message)