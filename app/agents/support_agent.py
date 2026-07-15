"""
app/agents/support_agent.py

Responsibility:
    - Receive a customer message and ID.
    - Detect the customer's intent (rule-based for Milestone 2).
    - Select and call the appropriate tool.
    - Return a structured AgentResponse.

Should NOT:
    - Call TicketService directly (must go through tools).
    - Return free-form strings (must return AgentResponse).
    - Own business rules (e.g., setting ticket status to OPEN).
    - Contain SQL, database logic, or prompt templates.

Architecture (Milestone 2 — State-Based):
    Customer Message
          ↓
    handle_message()   — initializes AgentState
          ↓
    _detect_intent()   — Node 1: reads state.message, writes state.intent
          ↓
    _route()           — Node 2: dispatches to correct handler via intent
          ↓
    _handle_*()        — Node 3: reads state, calls tool, writes tool results
          ↓
    _build_response()  — converts final internal state → external AgentResponse

Why state-based before LangGraph?
    LangGraph is fundamentally: State → Node → Updated State.
    Building this pattern manually means LangGraph's nodes, edges,
    and conditional routing become immediately recognizable rather
    than abstract framework concepts to memorize.

Key rule:
    AgentState  = internal pipeline object (never returned to callers).
    AgentResponse = external contract         (the only thing callers see).
"""

from typing import Callable

from app.schemas.agent import AgentResponse, Intent
from app.schemas.agent_state import AgentState
from app.agents.intent_classifier import classifier
from app.tools.ticket_tools import create_ticket_tool

# Type alias for handler functions (nodes).
# Every handler receives AgentState and returns AgentState.
# Signatures are now uniform — _route() doesn't need to know
# what arguments each handler needs; it just passes state through.
HandlerFn = Callable[[AgentState], AgentState]


class SupportAgent:
    """
    State-based customer support agent (Milestone 2).

    Each private method is a "node" in the workflow:
        - Receives AgentState.
        - Reads only what it needs from state.
        - Writes its output back onto state.
        - Returns the updated state.

    This mirrors LangGraph's node contract exactly.
    When we introduce LangGraph, each of these methods becomes
    a graph node with minimal changes required.

    Adding a new intent:
        1. Add keywords to the relevant keyword set.
        2. Add a _handle_new_intent(state) method.
        3. Add one entry to _INTENT_HANDLERS.
        _route(), handle_message(), and _build_response() never change.
    """

    # ------------------------------------------------------------------
    # Intent Detection Keywords
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Node 1 — Intent Detection
    # Reads:  state.message
    # Writes: state.intent
    # ------------------------------------------------------------------

    def _detect_intent(self, state: AgentState) -> AgentState:
        """
        Detect intent via keyword matching and write it onto state.

        Priority order (evaluated top to bottom):
            1. Refund   — financial impact, highest priority.
            2. Delivery — late/missing shipment context.
            3. Order    — wrong/damaged item issues.
            4. General  — fallback for anything unrecognised.

        LangGraph equivalent: a graph node that reads state and
        returns a new state with intent populated.
        """

        # Delegates to IntentClassifier — the single source of truth.
        # Keyword sets and priority order are defined only there.
        state.intent = classifier.classify(state.message)
        return state

    # ------------------------------------------------------------------
    # Node 3 variants — Intent Handlers
    # Each handler is a self-contained node.
    # Reads:  state.customer_id, state.message, state.intent
    # Writes: state.tool_used, state.ticket_id, state.response
    # ------------------------------------------------------------------

    def _handle_refund_request(self, state: AgentState) -> AgentState:
        ticket = create_ticket_tool(
            customer_id=state.customer_id,
            issue=state.message,
        )
        state.tool_used  = "create_ticket_tool"
        state.ticket_id  = ticket.ticket_id
        state.response   = (
            f"I've raised a refund request for you. "
            f"Your ticket ID is {ticket.ticket_id}. "
            f"Our team will review it and get back to you shortly."
        )
        return state

    def _handle_delivery_issue(self, state: AgentState) -> AgentState:
        ticket = create_ticket_tool(
            customer_id=state.customer_id,
            issue=state.message,
        )
        state.tool_used  = "create_ticket_tool"
        state.ticket_id  = ticket.ticket_id
        state.response   = (
            f"I've logged a delivery issue for you. "
            f"Your ticket ID is {ticket.ticket_id}. "
            f"We'll investigate and update you as soon as possible."
        )
        return state

    def _handle_order_issue(self, state: AgentState) -> AgentState:
        ticket = create_ticket_tool(
            customer_id=state.customer_id,
            issue=state.message,
        )
        state.tool_used  = "create_ticket_tool"
        state.ticket_id  = ticket.ticket_id
        state.response   = (
            f"I've created a support ticket for your order issue. "
            f"Your ticket ID is {ticket.ticket_id}. "
            f"A support specialist will follow up with you soon."
        )
        return state

    def _handle_general_inquiry(self, state: AgentState) -> AgentState:
        # No ticket created. No tool used.
        # tool_used and ticket_id remain None (default from AgentState).
        state.response = (
            "Thank you for reaching out. Could you provide more details "
            "about your issue so I can assist you better?"
        )
        return state

    # ------------------------------------------------------------------
    # Dispatch Table
    # Maps each Intent to its handler node.
    # _route() performs a single lookup — it never grows.
    #
    # Why @property?
    # Handlers are instance methods (self._handle_*), which require
    # self to exist. At class definition time, self doesn't exist yet,
    # so a class-level dict can't reference them directly.
    # A property resolves this cleanly.
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
    # Node 2 — Routing
    # Reads:  state.intent
    # Writes: delegates to the matched handler node
    # ------------------------------------------------------------------

    def _route(self, state: AgentState) -> AgentState:
        """
        Dispatch to the correct handler node via _INTENT_HANDLERS.

        Notice the signature change from Milestone 1:
            Before: _route(intent, customer_id, message) → AgentResponse
            After:  _route(state)                        → AgentState

        This method never grows. All routing knowledge lives in
        _INTENT_HANDLERS; _route() is just the mechanism.

        Falls back to _handle_general_inquiry defensively if an
        unmapped intent somehow arrives.

        LangGraph equivalent: a conditional edge that reads state.intent
        and routes to the matching node.
        """

        intent = state.intent
        if intent is None:
            handler = self._handle_general_inquiry
        else:
            handler = self._INTENT_HANDLERS.get(intent, self._handle_general_inquiry)
        return handler(state)

    # ------------------------------------------------------------------
    # State → Response Converter
    # Reads:  final AgentState
    # Returns: AgentResponse (external contract)
    #
    # This is the boundary between internal pipeline state and the
    # external API contract. Nothing above this line is visible to callers.
    # ------------------------------------------------------------------

    def _build_response(self, state: AgentState) -> AgentResponse:
        """
        Convert the completed internal AgentState into an AgentResponse.

        AgentState  = internal — carries full pipeline context.
        AgentResponse = external — the stable contract callers depend on.

        Keeping this conversion explicit in one place means the internal
        state structure can evolve (e.g., adding error fields, confidence
        scores, memory references) without changing the external contract.
        """

        return AgentResponse(
            intent=state.intent or Intent.GENERAL_INQUIRY,
            tool_used=state.tool_used,
            ticket_id=state.ticket_id,
            response=state.response or "",
            needs_human=state.needs_human,
        )

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

        Workflow (each step is a node operating on shared state):
            1. Initialize AgentState from caller inputs.
            2. _detect_intent(state)  — populate state.intent.
            3. _route(state)          — dispatch to handler node.
            4. _build_response(state) — convert state → AgentResponse.

        External signature is unchanged from Milestone 1.
        All existing validation tests pass without modification.
        Only the internal architecture changed.
        """

        state = AgentState(
            customer_id=customer_id,
            message=message,
        )

        state = self._detect_intent(state)
        state = self._route(state)

        return self._build_response(state)