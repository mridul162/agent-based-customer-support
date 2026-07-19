"""
app/schemas/tool_spec.py

Purpose:
--------
Define the ToolSpec dataclass — a single object that captures everything
needed to register, validate, execute, and respond for one tool.

Responsibilities:
-----------------
- Define type aliases for tool callables, argument builders, response builders.
- Define ToolSpec as a frozen dataclass (immutable after construction).

This module DOES NOT:
---------------------
- Register any tools (app/tools/tool_registry.py owns that).
- Execute tools.
- Read AgentState at runtime.
- Know about specific tools like create_ticket_tool or get_ticket_tool.

Why dataclass instead of Pydantic BaseModel?
--------------------------------------------
ToolSpec holds callables (tool_fn, argument_builder, response_builder).
Pydantic is designed for data validation — it serializes/deserializes values
and doesn't naturally hold arbitrary Python callables as typed fields.
A frozen dataclass is the right tool: it's immutable, lightweight, typed,
and supports callables without any friction.

Why frozen=True?
----------------
ToolSpec instances are module-level constants defined at import time.
They should never be mutated at runtime. `frozen=True` enforces this
at the language level — any attempt to assign to a field after
construction raises a FrozenInstanceError immediately.

Architecture context:
---------------------
Before Milestone 8, tool metadata was split across four locations:

    _TOOL_REGISTRY         in tool_executor_node.py
    _ARGUMENT_BUILDERS     in tool_executor_node.py
    _REQUIRED_ARGUMENTS    in argument_validation_node.py
    _RESPONSE_BUILDERS     in response_node.py

Adding one tool required edits in four files.

After Milestone 8, each tool is described by one ToolSpec instance
in one registry file. Every node reads from that single source:

    spec = TOOL_REGISTRY[tool_name]

    spec.tool_fn              → executor calls this
    spec.argument_builder     → executor uses this to build args
    spec.required_arguments   → validator checks these
    spec.response_builder     → response node calls this
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.schemas.agent_state import AgentState

# ---------------------------------------------------------------------------
# Type Aliases
#
# Named aliases make ToolSpec's field types readable at a glance
# and give type checkers enough information to catch mismatched callables.
# ---------------------------------------------------------------------------

# A tool function: takes keyword arguments, returns any value.
ToolFn = Callable[..., Any]

# Builds the keyword arguments dict passed to ToolFn.
# Reads from AgentState (customer_id, message, extracted_arguments, etc.).
ArgumentBuilder = Callable[[AgentState], dict[str, Any]]

# Converts a tool's raw return value into a customer-facing string.
# Receives tool_result directly — including None, which each builder
# interprets according to its tool's semantics.
ResponseBuilder = Callable[[Any], str]


# ---------------------------------------------------------------------------
# ToolSpec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolSpec:
    """
    Complete specification for one registered tool.

    Fields:
        name:               Tool name string — must match exactly what the
                            LLM returns in ToolDecision.tool_name.

        tool_fn:            The callable that executes the tool.
                            Receives keyword arguments from argument_builder.

        required_arguments: Names of arguments that must be present in
                            state.extracted_arguments before execution.
                            Empty tuple means no extraction is required
                            (arguments come from state fields directly).
                            Tuple (not list) signals immutability — this
                            configuration is fixed at registration time.

        argument_builder:   Builds the kwargs dict passed to tool_fn.
                            Reads from AgentState. May read state fields
                            (customer_id, message) or extracted_arguments.

        response_builder:   Converts tool_fn's return value into a
                            customer-facing string. Receives the raw
                            tool_result, including None.
    """

    name:               str
    tool_fn:            ToolFn
    required_arguments: tuple[str, ...]
    argument_builder:   ArgumentBuilder
    response_builder:   ResponseBuilder