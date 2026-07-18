"""
app/prompts/tool_decision_prompt.py

Purpose:
--------
Own the system prompt used by the LLM decision node to select a tool.

Responsibilities:
-----------------
- Define TOOL_DECISION_SYSTEM_PROMPT.
- Document what the prompt instructs the LLM to do.
- Be the single place to update when tool descriptions change.

This module DOES NOT:
---------------------
- Call the LLM.
- Parse LLM responses.
- Know about AgentState, nodes, or the graph.
- Contain business logic.

Why prompts deserve their own module:
--------------------------------------
As the system grows, prompts multiply:

    tool_decision_prompt.py     ← this file
    response_prompt.py          ← future: generate customer-facing responses
    escalation_prompt.py        ← future: decide escalation reasoning
    router_prompt.py            ← future: multi-agent routing

If prompts live inside nodes, they are scattered and hard to:
    - Review as a set
    - Version together
    - Test independently of node execution
    - Hand off to a prompt engineer

Keeping prompts in app/prompts/ makes the node purely orchestration
and the prompt purely instruction.

Design note — why no {arguments} instruction:
----------------------------------------------
The prompt instructs the LLM to return only tool_name and reasoning,
not arguments. This implements Design B from the architecture review:

    LLM owns:      tool_name, reasoning   (the decision)
    Executor owns: argument construction  (reading from state)

For create_ticket_tool(), customer_id and issue already exist in
state.customer_id and state.message. The LLM copying them into
arguments would be wasted tokens and an extra failure surface,
since the LLM didn't derive those values — the caller provided them.

Design A (LLM fills arguments) becomes correct when tools need values
the LLM extracts or derives — e.g., order_id from "my order 12345
never arrived." That capability is added when those tools exist.
"""

TOOL_DECISION_SYSTEM_PROMPT = """
You are a customer support AI agent.

Your job is to decide what action to take based on a customer's message.

Available tools:

1. create_ticket_tool
   Use this when the customer has a support issue that requires
   follow-up action: refund requests, delivery problems, order issues,
   billing errors, or any complaint that needs to be tracked.

2. get_ticket_tool
   Use this when the customer is asking about an existing ticket.
   Use when:
     - The customer asks about ticket status
     - The customer references an existing ticket ID (e.g. TICKET-123)
     - The customer wants an update on a previously created ticket
   Do NOT use for creating a new issue.

3. no_tool
   Use this only when no action is needed: greetings, thank-you messages,
   or messages that are clearly not support requests.

Instructions:
- Choose exactly ONE tool.
- Provide a short, specific reasoning explaining why you chose it.
- Do not include tool arguments — those are handled separately.

You MUST respond with a valid JSON object only.
No explanation. No markdown. No code fences. Just the JSON.

Response format:
{
  "tool_name": "create_ticket_tool" or "get_ticket_tool" or "no_tool",
  "reasoning": "one sentence explaining your choice"
}
""".strip()