"""
Ingest the customer-support markdown knowledge base into chunk artifacts.
"""

from collections import Counter
from pathlib import Path

from app.config.settings import settings
from app.rag.chunkers.semantic_chunker import SemanticChunker
from app.rag.loaders.markdown_loader import MarkdownLoader
from app.rag.parsers.markdown_parser import MarkdownParser
from app.rag.utils.artifact_writer import ArtifactWriter
from app.rag.utils.normalizer import TextNormalizer


class IngestionPipeline:
    """
    Main ingestion orchestrator for flat support KB markdown files.
    """

    def __init__(self, kb_root: str):
        self.kb_root = Path(kb_root)
        self.loader = MarkdownLoader(kb_root=str(self.kb_root))
        self.parser = MarkdownParser()
        self.normalizer = TextNormalizer()
        self.chunker = SemanticChunker()
        self.artifact_writer = ArtifactWriter(
            artifacts_root=settings.rag_artifacts_path
        )

    def run(self):
        """
        Execute ingestion and write parsed, normalized, and chunk artifacts.
        """

        self._print_pipeline_header()

        print("\n[STEP 1] Loading documents...\n")
        documents = self.loader.load()
        print(f"Loaded {len(documents)} documents.")

        total_sections = 0
        total_chunks = 0
        chunk_word_counts = []

        print("\n[STEP 2] Processing documents...\n")

        for index, document in enumerate(documents, start=1):
            print(
                f"[{index}/{len(documents)}] "
                f"{document.document_id} -> {document.file_type}"
            )

            base_metadata = {
                "document_id": document.document_id,
                "category": document.category,
                "source_file": f"{document.file_type}.md",
                "source_path": str(document.path),
            }

            parsed_sections = self.parser.parse(document.content)
            total_sections += len(parsed_sections)

            self.artifact_writer.write_parsed_sections(
                sections=parsed_sections,
                category=document.category,
                product_id=document.document_id,
                source_file=document.file_type,
            )

            normalized_sections = self.normalizer.normalize_sections(parsed_sections)

            self.artifact_writer.write_normalized_sections(
                sections=normalized_sections,
                category=document.category,
                product_id=document.document_id,
                source_file=document.file_type,
            )

            chunks = self.chunker.chunk_sections(
                sections=normalized_sections,
                base_metadata=base_metadata,
            )

            total_chunks += len(chunks)
            chunk_word_counts.extend(chunk.metadata["word_count"] for chunk in chunks)

            self.artifact_writer.write_chunks(
                chunks=chunks,
                category=document.category,
                product_id=document.document_id,
                source_file=document.file_type,
            )

        self._print_pipeline_summary(
            documents=documents,
            total_sections=total_sections,
            total_chunks=total_chunks,
            chunk_word_counts=chunk_word_counts,
        )

        self.artifact_writer.write_pipeline_log(
            {
                "documents_processed": len(documents),
                "sections_generated": total_sections,
                "chunks_generated": total_chunks,
                "status": "success",
            }
        )

        print("\n[PIPELINE COMPLETED SUCCESSFULLY]")

    def _print_pipeline_header(self):
        print("\n" + "=" * 70)
        print("CUSTOMER SUPPORT KB INGESTION PIPELINE")
        print("=" * 70)
        print("\nKB Root:")
        print(self.kb_root)

    def _print_pipeline_summary(
        self,
        documents,
        total_sections,
        total_chunks,
        chunk_word_counts,
    ):
        print("\n" + "=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"\nDocuments Processed : {len(documents)}")
        print(f"Sections Generated  : {total_sections}")
        print(f"Chunks Generated    : {total_chunks}")

        if chunk_word_counts:
            print("\nChunk Word Counts:")
            print(f"  Min: {min(chunk_word_counts)}")
            print(f"  Max: {max(chunk_word_counts)}")
            print(f"  Avg: {sum(chunk_word_counts) / len(chunk_word_counts):.2f}")

        category_counter = Counter(doc.category for doc in documents)

        print("\nCategory Distribution:")
        for category, count in sorted(category_counter.items()):
            print(f"  - {category}: {count}")

        print("\nArtifacts Written To:")
        print("  artifacts/parsed/")
        print("  artifacts/normalized/")
        print("  artifacts/chunked/")
        print("  artifacts/pipeline_logs/")


if __name__ == "__main__":
    pipeline = IngestionPipeline(kb_root=settings.knowledge_base_path)
    pipeline.run()
