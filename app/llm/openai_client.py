"""
app/llm/openai_client.py

Purpose:
--------
Single source of truth for OpenAI client construction.

Responsibilities:
-----------------
- Construct and return a configured OpenAI client.
- Read API key from settings (never hardcoded).
- Expose one function that any node or service can import.

This module DOES NOT:
---------------------
- Make LLM calls.
- Own prompts.
- Know about agents, nodes, or tools.
- Manage conversation history or memory.

Why this file exists:
---------------------
Without this, every node that needs an LLM call constructs its own client:

    # llm_decision_node.py
    _client = OpenAI(api_key=settings.openai_api_key)

    # response_node.py
    _client = OpenAI(api_key=settings.openai_api_key)

    # escalation_node.py
    _client = OpenAI(api_key=settings.openai_api_key)

When the provider changes (Azure OpenAI, Anthropic, local model),
every node must be updated.

With this file, all nodes import one function:

    from app.llm.openai_client import get_openai_client

and only this file changes when the provider changes.
"""

from openai import OpenAI

from app.config.settings import settings


def get_openai_client() -> OpenAI:
    """
    Construct and return a configured OpenAI client.

    Called at the point of use (inside nodes/services), not at
    module import time, so configuration is always read from the
    current settings state. This also makes testing easier —
    tests can patch settings before calling this function.

    Returns:
        OpenAI: Configured client instance.
    """
    return OpenAI(api_key=settings.openai_api_key)