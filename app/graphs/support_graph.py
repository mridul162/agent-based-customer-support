"""
app/graphs/support_graph.py

Purpose:
--------
Define and compile the LangGraph-based support workflow.

This file translates the manual pipeline built in SupportAgent (Milestone 2)
into a formal graph structure — making execution flow explicit as graph
edges rather than implicit as Python method calls.

Responsibilities:
-----------------
- Define graph nodes (functions that read state, perform work, update state).
- Define the routing function (reads state, returns next node name — no state changes).
- Register nodes and edges with the StateGraph.
- Compile and expose the runnable graph.

This module DOES NOT:
---------------------
- Detect intent (that logic lives in SupportAgent / node functions).
- Execute tool calls (that logic lives in ticket_tools.py).
- Own business rules (those live in TicketService).
- Build API responses (AgentResponse is constructed at the boundary layer).
- Manage memory, retrieval, or multi-agent orchestration (future milestones).

Relationship to SupportAgent:
------------------------------
SupportAgent (Milestone 2) implemented the same workflow manually:

    handle_message()
          ↓
    _detect_intent(state)     ← becomes: detect_intent node
          ↓
    _route(state)             ← becomes: conditional edge via route_by_intent()
          ↓
    _handle_*(state)          ← becomes: refund / delivery / order / general nodes
          ↓
    _build_response(state)    ← becomes: caller's responsibility post-graph

The key architectural insight being applied here:
    Routing does not modify state.
    It only determines execution flow.
    Therefore it belongs in a conditional edge, not in a node.

    Node     = work  (reads state → performs work → updates state)
    Edge     = flow  (reads state → returns next node name → no state change)

LangGraph execution model:
--------------------------
    START
      ↓
    detect_intent          ← Node: writes state.intent
      ↓
    conditional edge       ← Routing function: reads state.intent, returns node name
      ├── "refund"   →  refund_node
      ├── "delivery" →  delivery_node
      ├── "order"    →  order_node
      └── "general"  →  general_node
      ↓
    END
"""

from langgraph.graph import END, START, StateGraph

from app.agents.intent_classifier import classifier
from app.schemas.agent_state import AgentState
from app.tools.ticket_tools import create_ticket_tool
from app.schemas.agent import Intent
from langgraph.graph.state import CompiledStateGraph

# ---------------------------------------------------------------------------
# Node: detect_intent
#
# Contract:
#   Reads:  state.message
#   Writes: state.intent
#   Does NOT route — routing is the graph's responsibility, not this node's.
#
# LangGraph node contract: (state) -> updated_state
# ---------------------------------------------------------------------------

def detect_intent_node(state: AgentState) -> AgentState:
    """
    Node 1 — Detect customer intent from the message.

    Keyword priority order:
        1. Refund   — financial impact, highest priority.
        2. Delivery — late/missing shipment context.
        3. Order    — wrong/damaged item issues.
        4. General  — fallback for anything unrecognised.

    This node performs real work (populates state.intent).
    It does not decide what comes next — that is the conditional edge's job.
    """

    # Delegates to IntentClassifier — the single source of truth.
    # Keyword sets and priority order are defined only there.
    state.intent = classifier.classify(state.message)
    return state


# ---------------------------------------------------------------------------
# Routing Function: route_by_intent
#
# This is NOT a node.
# It does NOT modify state.
# It ONLY reads state.intent and returns the name of the next node.
#
# LangGraph conditional edge contract: (state) -> str
#
# Why a string return instead of an Intent enum?
# LangGraph maps the returned string to a registered node name.
# Keeping these as plain strings makes the graph wiring explicit and readable.
# ---------------------------------------------------------------------------

def route_by_intent(state: AgentState) -> str:
    """
    Routing function — determines which handler node executes next.

    Reads state.intent (written by detect_intent_node).
    Returns the name of the next node as a string.
    Does not update state.

    The string values returned here must match exactly the node names
    registered in the graph via add_node().
    """

    routing_map: dict[Intent, str] = {
        Intent.REFUND_REQUEST:  "refund_node",
        Intent.DELIVERY_ISSUE:  "delivery_node",
        Intent.ORDER_ISSUE:     "order_node",
        Intent.GENERAL_INQUIRY: "general_node",
    }
    
    if state.intent is None:
        return "general_node"

    # Falls back to "general_node" if an unmapped intent arrives.
    # Defensive — not speculative.
    return routing_map.get(state.intent, "general_node")


# ---------------------------------------------------------------------------
# Handler Nodes
#
# Each node follows the same contract:
#   Reads:  state.customer_id, state.message
#   Calls:  one tool
#   Writes: state.tool_used, state.ticket_id, state.response
#   Returns: updated state
#
# Design rule applied here:
#   Graph Node → Tool → Service
#   NOT: Graph Node → Agent → Tool (two orchestration layers)
#
# The graph is now the orchestrator.
# SupportAgent's handlers are no longer called — this replaces them.
# ---------------------------------------------------------------------------

def refund_node(state: AgentState) -> AgentState:
    """
    Node: handle refund request.

    Reads:  state.customer_id, state.message
    Writes: state.tool_used, state.ticket_id, state.response
    """
    ticket = create_ticket_tool(
        customer_id=state.customer_id,
        issue=state.message,
    )
    state.tool_used = "create_ticket_tool"
    state.ticket_id = ticket.ticket_id
    state.response  = (
        f"I've raised a refund request for you. "
        f"Your ticket ID is {ticket.ticket_id}. "
        f"Our team will review it and get back to you shortly."
    )
    return state


def delivery_node(state: AgentState) -> AgentState:
    """
    Node: handle delivery issue.

    Reads:  state.customer_id, state.message
    Writes: state.tool_used, state.ticket_id, state.response
    """
    ticket = create_ticket_tool(
        customer_id=state.customer_id,
        issue=state.message,
    )
    state.tool_used = "create_ticket_tool"
    state.ticket_id = ticket.ticket_id
    state.response  = (
        f"I've logged a delivery issue for you. "
        f"Your ticket ID is {ticket.ticket_id}. "
        f"We'll investigate and update you as soon as possible."
    )
    return state


def order_node(state: AgentState) -> AgentState:
    """
    Node: handle order issue.

    Reads:  state.customer_id, state.message
    Writes: state.tool_used, state.ticket_id, state.response
    """
    ticket = create_ticket_tool(
        customer_id=state.customer_id,
        issue=state.message,
    )
    state.tool_used = "create_ticket_tool"
    state.ticket_id = ticket.ticket_id
    state.response  = (
        f"I've created a support ticket for your order issue. "
        f"Your ticket ID is {ticket.ticket_id}. "
        f"A support specialist will follow up with you soon."
    )
    return state


def general_node(state: AgentState) -> AgentState:
    """
    Node: handle general inquiry.

    No tool called. No ticket created.
    tool_used and ticket_id remain None (AgentState defaults).

    Reads:  nothing (no tool needed)
    Writes: state.response
    """
    state.response = (
        "Thank you for reaching out. Could you provide more details "
        "about your issue so I can assist you better?"
    )
    return state


# ---------------------------------------------------------------------------
# Graph Construction
#
# Build order:
#   1. Declare graph with its state schema.
#   2. Register all nodes.
#   3. Define edges (START → detect_intent → conditional edge → handler → END).
#   4. Compile into a runnable.
# ---------------------------------------------------------------------------

def build_support_graph() -> CompiledStateGraph:
    """
    Construct and compile the customer support workflow graph.

    Graph structure:
        START → detect_intent → [conditional edge] → handler → END

    Returns the compiled graph, ready to invoke with:
        graph.invoke({"customer_id": ..., "message": ...})
    """

    graph = StateGraph(AgentState)

    # ------------------------------------------------------------------
    # Register Nodes
    # String names must match exactly what route_by_intent() returns.
    # ------------------------------------------------------------------

    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("refund_node",   refund_node)
    graph.add_node("delivery_node", delivery_node)
    graph.add_node("order_node",    order_node)
    graph.add_node("general_node",  general_node)

    # ------------------------------------------------------------------
    # Define Edges
    # ------------------------------------------------------------------

    graph.add_edge(START, "detect_intent")

    graph.add_conditional_edges(
        "detect_intent",
        route_by_intent,
        {
            "refund_node":   "refund_node",
            "delivery_node": "delivery_node",
            "order_node":    "order_node",
            "general_node":  "general_node",
        },
    )

    for handler_node in ("refund_node", "delivery_node", "order_node", "general_node"):
        graph.add_edge(handler_node, END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Module-level compiled graph instance.
# Imported and invoked by the API layer or tests.
# ---------------------------------------------------------------------------

support_graph = build_support_graph()