"""
answer_generator.py

Purpose:
--------
Generate final answers from retrieved context.

Responsibilities:
-----------------
- Execute retrieval
- Build prompts from retrieved chunks
- Call the generation model
- Return the generated answer

This module DOES NOT:
---------------------
- perform chunking
- create embeddings
- manage vector indexes
- rerank results
- manage conversation memory
- evaluate answer quality
- perform prompt formatting logic

Architecture Philosophy:
------------------------
Thin orchestration layer.

RetrievalPipeline finds information.
PromptBuilder structures information.
The LLM generates the answer.

Keep generation logic simple,
observable, and easy to extend.
"""

from app.config.settings import settings
from app.llm.llm_service import LLMService
from app.rag.generators.prompt_builder import PromptBuilder
from app.rag.pipelines.retrieval_pipeline import RetrievalPipeline
from app.schemas.execution_trace import ExecutionTrace


class AnswerGenerator:
    """
    End-to-end answer generation service.
    """

    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        model_name: str | None = None,
    ):
        self.retrieval_pipeline = retrieval_pipeline
        self.prompt_builder = PromptBuilder()

        self.model_name = model_name or settings.openai_model

    def generate(
        self,
        query: str,
        history:None,
        top_k: int = 5,
        execution_trace: ExecutionTrace | None = None,
    ) -> str:
        """
        Generate an answer for a user query.

        Flow:
            Query
              ↓
            Retrieval
              ↓
            Retrieved Chunks
              ↓
            Prompt Builder
              ↓
            GPT-4.1-mini
              ↓
            Answer
        """

        retrieved_chunks = self.retrieval_pipeline.retrieve(
            query=query,
            top_k=top_k,
        )

        messages = self.prompt_builder.build_messages(
            query=query,
            chunks=retrieved_chunks,
            history=history,
        )

        response = LLMService.create_chat_completion(
            model=self.model_name,
            messages=messages,
            temperature=0.1,
            execution_trace=execution_trace,
            node_name="answer_generator",
        )

        answer = response.choices[0].message.content

        return answer.strip()
    

if __name__ == "__main__":

    from app.rag.embedders.openai_embedder import OpenAIEmbedder
    from app.rag.pipelines.retrieval_pipeline import RetrievalPipeline
    from app.rag.retrievers.retriever import Retriever
    from app.rag.vectorstores.faiss_store import FAISSStore

    # Load embedder
    embedder = OpenAIEmbedder(
        model_name="text-embedding-3-small"
    )

    # Load vector store
    vector_store = FAISSStore(
        embedding_dimension=1536
    )

    vector_store.load(
        index_path=settings.faiss_index_path,
        metadata_path=settings.faiss_metadata_path,
    )

    # Create retriever
    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    # Create retrieval pipeline
    retrieval_pipeline = RetrievalPipeline()

    # Create answer generator
    generator = AnswerGenerator(
        retrieval_pipeline=retrieval_pipeline
    )

    # Test queries
    test_queries = [
        "500g lichu fuler modhur dam koto?"
    ]

    for query in test_queries:

        print("\n" + "=" * 80)
        print(f"QUERY:\n{query}")
        print("=" * 80)

        answer = generator.generate(
            query=query,
            top_k=5,
        )

        print("\nANSWER:\n")
        print(answer)
        print()
