"""
tests/validate_grounded_answer_generation.py

Purpose:
--------
Validate grounded answer generation through:

AnswerGenerator -> RetrievalPipeline -> PromptBuilder -> LLMService

This developer validation avoids live OpenAI calls by patching the OpenAI
client used inside LLMService. The important assertion is architectural:
grounded answer generation must go through LLMService so LLMMetrics are
recorded in ExecutionTrace.
"""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.generators.answer_generator import AnswerGenerator
from app.rag.models.retrieval_models import RetrievedChunk
from app.schemas.execution_trace import ExecutionTrace

PASS = "PASS"
FAIL = "FAIL"


def check(condition: bool, message: str) -> None:
    status = PASS if condition else FAIL
    symbol = "[OK]" if condition else "[FAIL]"
    print(f"  {symbol} {status:<6} {message}")

    if not condition:
        raise AssertionError(message)


class FakeRetrievalPipeline:
    """
    Return deterministic retrieved chunks for grounding scenarios.
    """

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        lowered = query.lower()

        if "refund" in lowered:
            return [
                RetrievedChunk(
                    chunk_id="returns_refund__refund.md__0__0",
                    text=(
                        "Refund requests are reviewed after the returned "
                        "item is received. Approved refunds are returned "
                        "to the original payment method."
                    ),
                    score=0.98,
                    metadata={
                        "document_id": "returns_refund",
                        "category": "returns",
                        "source_file": "refund.md",
                        "heading": "Refund Policy",
                    },
                )
            ]

        if "shipping" in lowered:
            return [
                RetrievedChunk(
                    chunk_id="shipping_shipping__shipping.md__0__0",
                    text=(
                        "Standard shipping delivery usually takes 3-5 "
                        "business days after an order is dispatched."
                    ),
                    score=0.96,
                    metadata={
                        "document_id": "shipping_shipping",
                        "category": "shipping",
                        "source_file": "shipping.md",
                        "heading": "Shipping Timeline",
                    },
                )
            ]

        return []


class FakeChatCompletions:
    """
    Offline chat-completion fake that follows the grounding rule.
    """

    def create(self, **kwargs):
        prompt = kwargs["messages"][-1]["content"].lower()

        if "no relevant context found" in prompt:
            answer = (
                "I couldn't find that information in the knowledge base. "
                "I can create a support ticket so a specialist can help."
            )
        elif "refund" in prompt:
            answer = (
                "Refund requests are reviewed after the returned item is "
                "received. Approved refunds are returned to the original "
                "payment method."
            )
        elif "shipping" in prompt:
            answer = (
                "Standard shipping delivery usually takes 3-5 business days "
                "after an order is dispatched."
            )
        else:
            answer = "I couldn't find that information in the knowledge base."

        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=answer))],
            usage=SimpleNamespace(
                prompt_tokens=120,
                completion_tokens=35,
                total_tokens=155,
            ),
        )


class FakeOpenAIClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeChatCompletions())


def build_trace() -> ExecutionTrace:
    return ExecutionTrace(
        request_id=str(uuid4()),
        customer_id="customer-grounded-validation",
        started_at=datetime.now(UTC),
    )


def generate_answer(
    question: str,
) -> tuple[str, ExecutionTrace, float]:
    trace = build_trace()
    generator = AnswerGenerator(
        retrieval_pipeline=FakeRetrievalPipeline(),  # type: ignore
        model_name="gpt-4o-mini",
    )

    with patch(
        "app.llm.llm_service.get_openai_client",
        return_value=FakeOpenAIClient(),
    ):
        started = time.perf_counter()
        answer = generator.generate(
            query=question,
            history=None,
            top_k=5,
            execution_trace=trace,
        )
        latency_ms = (time.perf_counter() - started) * 1000

    return answer, trace, latency_ms


def validate_refund_answer() -> None:
    print("[1] Refund grounded answer")

    answer, trace, _ = generate_answer("What is your refund policy?")
    lowered = answer.lower()

    check(answer.strip() != "", "Answer generated")
    check("refund" in lowered, "Answer mentions refund")
    check(
        "couldn't find that information" not in lowered,
        "No hallucination fallback for known refund answer",
    )
    check(len(trace.llm_metrics) == 1, "LLM metrics recorded")


def validate_shipping_answer() -> None:
    print("[2] Shipping grounded answer")

    answer, _, _ = generate_answer("How long does shipping take?")
    lowered = answer.lower()

    check("shipping" in lowered, "Answer mentions shipping")
    check("delivery" in lowered, "Answer mentions delivery")
    check("business days" in lowered, "Answer mentions business days")


def validate_unknown_answer() -> None:
    print("[3] Unknown grounded answer")

    answer, _, _ = generate_answer("What is your office location in New York?")
    lowered = answer.lower()

    check(
        "couldn't find that information in the knowledge base" in lowered,
        "Unknown answer uses knowledge-base fallback",
    )
    check("new york" not in lowered, "Answer does not invent New York office")


def validate_latency() -> None:
    print("[4] Latency")

    answer, _, latency_ms = generate_answer("What is your refund policy?")

    check(answer.strip() != "", "Grounded answer returned")
    check(latency_ms >= 0, "Latency measured")

    print(f"  Grounded Answer : {answer}")
    print(f"  Latency         : {latency_ms:.2f} ms")


def validate_observability() -> None:
    print("[5] Observability")

    _, trace, _ = generate_answer("What is your refund policy?")

    check(len(trace.llm_metrics) == 1, "Exactly one LLM metric recorded")

    llm = trace.llm_metrics[0]

    check(llm.success, "LLM execution marked successful")
    check(llm.prompt_tokens == 120, "Prompt tokens recorded")
    check(llm.completion_tokens == 35, "Completion tokens recorded")
    check(llm.total_tokens == 155, "Total tokens recorded")
    check(llm.estimated_cost_usd is not None, "Cost estimated")
    check(llm.node_name == "answer_generator", "Node name recorded")


def main() -> None:
    print("=" * 68)
    print("  Grounded Answer Generation Validation")
    print("=" * 68)
    print()

    validate_refund_answer()
    print()

    validate_shipping_answer()
    print()

    validate_unknown_answer()
    print()

    validate_latency()
    print()

    validate_observability()
    print()

    print("=" * 68)
    print("  Grounded Answer Generation Completed")
    print("=" * 68)


if __name__ == "__main__":
    main()
