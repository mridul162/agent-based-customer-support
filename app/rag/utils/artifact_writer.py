"""
artifact_writer.py

Purpose:
--------
Persist ingestion pipeline artifacts for debugging,
inspection, observability, and retrieval evaluation.

Responsibilities:
-----------------
- Write parsed section artifacts
- Write normalized section artifacts
- Write chunk artifacts
- Create directory structure automatically
- Save UTF-8 multilingual-safe JSON artifacts

This writer DOES NOT:
---------------------
- validate artifacts
- compress artifacts
- version artifacts
- manage databases
- generate embeddings

Architecture Philosophy:
------------------------
Observability first.
Simple JSON artifacts.
Human-inspectable outputs.
"""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from typing import List


# ---------------------------------------------------------
# ARTIFACT WRITER
# ---------------------------------------------------------

class ArtifactWriter:
    """
    Writes ingestion artifacts to disk.
    """

    def __init__(
        self,
        artifacts_root: str = "artifacts"
    ):

        self.artifacts_root = Path(
            artifacts_root
        )

        self._initialize_directories()

    # -----------------------------------------------------

    def write_parsed_sections(
        self,
        sections,
        category: str,
        product_id: str,
        source_file: str,
    ):
        """
        Persist parsed semantic sections.
        """

        artifact_data = []

        for section in sections:

            artifact_data.append({

                "heading": (
                    section.heading
                ),

                "level": (
                    section.level
                ),

                "section_id": (
                    section.section_id
                ),

                "heading_path": (
                    section.heading_path
                ),

                "content": (
                    section.content
                ),
            })

        output_path = (
            self.artifacts_root
            / "parsed"
            / category
            / product_id
            / f"{source_file}.json"
        )

        self._write_json(
            output_path,
            artifact_data
        )

    # -----------------------------------------------------

    def write_normalized_sections(
        self,
        sections,
        category: str,
        product_id: str,
        source_file: str,
    ):
        """
        Persist normalized sections.
        """

        artifact_data = []

        for section in sections:

            artifact_data.append({

                "heading": (
                    section.heading
                ),

                "level": (
                    section.level
                ),

                "section_id": (
                    section.section_id
                ),

                "heading_path": (
                    section.heading_path
                ),

                "content": (
                    section.content
                ),
            })

        output_path = (
            self.artifacts_root
            / "normalized"
            / category
            / product_id
            / f"{source_file}.json"
        )

        self._write_json(
            output_path,
            artifact_data
        )

    # -----------------------------------------------------

    def write_chunks(
        self,
        chunks,
        category: str,
        product_id: str,
        source_file: str,
    ):
        """
        Persist semantic retrieval chunks.
        """

        artifact_data = []

        for chunk in chunks:

            artifact_data.append({

                "chunk_id": (
                    chunk.chunk_id
                ),

                "text": (
                    chunk.text
                ),

                "metadata": (
                    chunk.metadata
                ),
            })

        output_path = (
            self.artifacts_root
            / "chunked"
            / category
            / product_id
            / f"{source_file}.json"
        )

        self._write_json(
            output_path,
            artifact_data
        )

    # -----------------------------------------------------

    def write_pipeline_log(
        self,
        log_data,
        filename: str = "pipeline_log.json",
    ):
        """
        Persist pipeline execution logs.
        """

        output_path = (
            self.artifacts_root
            / "pipeline_logs"
            / filename
        )

        self._write_json(
            output_path,
            log_data
        )

    # -----------------------------------------------------

    def _write_json(
        self,
        output_path: Path,
        data,
    ):
        """
        Write UTF-8 safe JSON artifact.
        """

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    # -----------------------------------------------------

    def _initialize_directories(
        self
    ):
        """
        Create artifact directory structure.
        """

        directories = [

            "parsed",

            "normalized",

            "chunked",

            "pipeline_logs",
        ]

        for directory in directories:

            path = (
                self.artifacts_root
                / directory
            )

            path.mkdir(
                parents=True,
                exist_ok=True,
            )


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    from dataclasses import dataclass
    from typing import Dict, Any, Optional

    # -----------------------------------------------------
    # Mock Models
    # -----------------------------------------------------

    @dataclass
    class ParsedSection:

        heading: str
        level: int
        content: str
        heading_path: List[str]
        section_id: Optional[str] = None

    @dataclass
    class Chunk:

        chunk_id: str
        text: str
        metadata: Dict[str, Any]

    # -----------------------------------------------------
    # Sample Data
    # -----------------------------------------------------

    sections = [

        ParsedSection(

            heading="Benefits",

            level=2,

            section_id="benefits",

            heading_path=[
                "Overview",
                "Benefits"
            ],

            content=(
                "Rich in natural antioxidants."
            )
        )
    ]

    chunks = [

        Chunk(

            chunk_id="chunk_001",

            text=(
                "Rich in natural antioxidants."
            ),

            metadata={

                "product_id": (
                    "kholisha_honey"
                ),

                "category": "honey",

                "source_file": (
                    "benefits.md"
                ),
            }
        )
    ]

    # -----------------------------------------------------
    # Execute Writer
    # -----------------------------------------------------

    writer = ArtifactWriter()

    writer.write_parsed_sections(

        sections=sections,

        product_id="kholisha_honey",

        source_file="benefits"
    )

    writer.write_normalized_sections(

        sections=sections,

        product_id="kholisha_honey",

        source_file="benefits"
    )

    writer.write_chunks(

        chunks=chunks,

        product_id="kholisha_honey",

        source_file="benefits"
    )

    writer.write_pipeline_log({

        "status": "success",

        "documents_processed": 1,
    })

    print("\nArtifacts written successfully.")