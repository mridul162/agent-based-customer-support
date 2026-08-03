"""
app/llm/pricing.py

Purpose:
--------
Estimate the monetary cost of a single LLM inference request.

This module centralizes provider pricing so the rest of the system never
needs to know how inference costs are calculated.

Given an LLM provider, model, and token usage, this module returns the
estimated inference cost in USD.

Responsibilities:
-----------------
- Store provider pricing metadata.
- Estimate request cost from token usage.
- Hide pricing implementation details.
- Return zero for unsupported models.

This module DOES NOT:
---------------------
- Execute LLM requests.
- Record observability metrics.
- Query provider pricing APIs.
- Perform currency conversion.
- Manage billing.

Architecture:
-------------
LLMService
      │
      ▼
estimate_cost(...)
      │
      ▼
Pricing Table
      │
      ▼
Estimated Cost (USD)

Pricing Formula:
----------------
Estimated Cost =

    (Prompt Tokens / 1,000,000 × Prompt Price)

          +

    (Completion Tokens / 1,000,000 × Completion Price)

Prices are expressed in USD per one million tokens.

Future Extensions:
------------------
Later milestones may extend this module with:

- Dynamic provider pricing
- Currency conversion
- Cached pricing metadata
- Enterprise pricing tiers
- Historical pricing versions
- Provider-specific discounts
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """
    Pricing information for one LLM model.

    Prices are expressed in USD per one million tokens.
    """

    input_price: float
    output_price: float


# ---------------------------------------------------------------------------
# Pricing Table
#
# Prices are USD per 1M tokens.
#
# Update this table whenever provider pricing changes.
# ---------------------------------------------------------------------------

PRICING: dict[str, dict[str, ModelPricing]] = {
    "openai": {
        "gpt-4o": ModelPricing(input_price=2.50, output_price=10.00),
        "gpt-4o-mini": ModelPricing(input_price=0.15, output_price=0.60),
    },
    # "anthropic": {...},
    # "google": {...},
}


def estimate_cost(
    *,
    provider: str,
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """
    Estimate the cost of one LLM request.

    Args:
        provider:
            LLM provider name.

        model:
            Model name.

        prompt_tokens:
            Number of prompt tokens.

        completion_tokens:
            Number of completion tokens.

    Returns:
        Estimated request cost in USD.

        Returns None if pricing information is unavailable.
    """

    if prompt_tokens is None or completion_tokens is None:
        return None

    provider = provider.lower()

    if provider != "openai":
        return None

    pricing = PRICING.get(provider, {}).get(model)

    if pricing is None:
        return None

    input_cost = (prompt_tokens / 1_000_000) * pricing.input_price

    output_cost = (completion_tokens / 1_000_000) * pricing.output_price

    return round(
        input_cost + output_cost,
        8,
    )
