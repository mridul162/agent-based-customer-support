"""
markdown_loader.py

Purpose:
--------
Load markdown knowledge-base documents from the filesystem and
convert them into structured RawDocument objects.

Responsibilities:
-----------------
- Discover markdown files
- Extract filesystem metadata
- Read markdown content
- Return structured document objects

This loader DOES NOT:
---------------------
- parse markdown
- clean content
- chunk text
- generate embeddings
- normalize text

Those responsibilities belong to later ingestion stages.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------


@dataclass
class RawDocument:
    """
    Represents a raw markdown document loaded from the KB.
    """

    document_id: str
    category: str
    file_type: str
    path: Path
    content: str


# ---------------------------------------------------------
# MARKDOWN LOADER
# ---------------------------------------------------------


class MarkdownLoader:
    """
    Filesystem markdown loader for the customer support knowledge base.
    """

    # Files/folders to ignore during loading
    IGNORED_FOLDERS = {
        "media",
        "translations",
        "qa",
        "__pycache__",
    }

    IGNORED_FILES = {"aliases.md"}

    def __init__(self, kb_root: str):
        """
        Parameters
        ----------
        kb_root : str
            Root path of the knowledge base.
        """

        self.kb_root = Path(kb_root)

        if not self.kb_root.exists():
            raise FileNotFoundError(
                f"Knowledge base path does not exist: {self.kb_root}"
            )

    # -----------------------------------------------------

    def load(self) -> list[RawDocument]:
        """
        Load all markdown documents from the KB.

        Returns
        -------
        List[RawDocument]
        """

        documents = []

        markdown_files = self._discover_markdown_files()

        for file_path in markdown_files:
            try:
                document = self._build_document(file_path)
                if document:
                    documents.append(document)
                    logger.info(f"Successfully loaded {file_path}")

            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        return documents

    # -----------------------------------------------------

    def _discover_markdown_files(self) -> list[Path]:
        """
        Discover all valid markdown files recursively.
        """

        markdown_files = []

        for file_path in self.kb_root.rglob("*.md"):
            # Skip ignored folders
            if any(folder in file_path.parts for folder in self.IGNORED_FOLDERS):
                continue

            # Skip ignored files
            if file_path.name in self.IGNORED_FILES:
                continue

            markdown_files.append(file_path)

        return sorted(markdown_files)

    # -----------------------------------------------------

    def _build_document(self, file_path: Path):

        content = self._read_markdown(file_path)

        # Skip empty files
        if not content.strip():
            return None

        category, document_id, file_type = self._extract_path_metadata(file_path)

        return RawDocument(
            document_id=document_id,
            category=category,
            file_type=file_type,
            path=file_path,
            content=content,
        )

    # -----------------------------------------------------

    def _read_markdown(self, file_path: Path) -> str:
        """
        Read markdown file safely using UTF-8 encoding.
        """

        return file_path.read_text(encoding="utf-8")

    # -----------------------------------------------------

    def _extract_path_metadata(self, file_path: Path):
        """
        Extract metadata from KB filesystem structure.

        Expected structure:
        -------------------

        knowledge_base/
            shipping/
                shipping.md

        Extracted:
        ----------
        category    -> shipping
        document_id -> shipping_shipping
        file_type   -> shipping
        """

        relative_path = file_path.relative_to(self.kb_root)

        parts = relative_path.parts

        if len(parts) < 2:
            raise ValueError(f"Invalid KB structure for file: {file_path}")

        category = parts[0]
        file_type = file_path.stem
        document_id = "_".join([*parts[:-1], file_path.stem]).replace(" ", "_").lower()

        return category, document_id, file_type


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    loader = MarkdownLoader(kb_root="knowledge_base")

    documents = loader.load()

    print("\n" + "=" * 60)
    print("MARKDOWN LOADER SUMMARY")
    print("=" * 60)

    print(f"Loaded documents: {len(documents)}")

    if documents:
        sample = documents[0]

        print("\nSample Document")
        print("-" * 60)

        print(f"Document ID: {sample.document_id}")
        print(f"Category   : {sample.category}")
        print(f"File Type  : {sample.file_type}")
        print(f"Path       : {sample.path}")

        print("\nContent Preview:")
        print(sample.content[:500])
