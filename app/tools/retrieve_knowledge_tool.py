"""
Tool for answering knowledge-base questions with RAG.
"""


def retrieve_knowledge_tool(
    question: str,
    execution_trace=None,
) -> str:
    """
    Retrieve relevant KB context and generate a customer-facing answer.
    """

    from app.services.retrieval_service import RetrievalService

    return RetrievalService.answer_question(
        question,
        execution_trace=execution_trace,
    )
