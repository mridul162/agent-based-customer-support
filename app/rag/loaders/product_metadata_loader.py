"""
product_metadata_loader.py

Purpose:
--------
Load product-level metadata from product.yaml files and convert
them into structured ProductMetadata objects.

Responsibilities:
-----------------
- Discover product.yaml files
- Load YAML safely
- Extract filesystem metadata
- Return structured metadata objects

This loader DOES NOT:
---------------------
- validate schema correctness
- merge chunk metadata
- enrich metadata
- generate aliases/tags
- normalize metadata

Those responsibilities belong to later ingestion stages.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8") #type: ignore

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List
import logging

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------

@dataclass
class ProductMetadata:
    """
    Represents product-level metadata loaded from product.yaml
    """

    product_id: str
    category: str
    path: Path
    metadata: Dict[str, Any]


# ---------------------------------------------------------
# PRODUCT METADATA LOADER
# ---------------------------------------------------------

class ProductMetadataLoader:
    """
    Loads product.yaml metadata files from the KB.
    """

    METADATA_FILENAME = "product.yaml"

    def __init__(self, kb_root: str):

        self.kb_root = Path(kb_root)

        if not self.kb_root.exists():
            raise FileNotFoundError(
                f"Knowledge base path does not exist: {self.kb_root}"
            )

    # -----------------------------------------------------

    def load(self) -> List[ProductMetadata]:
        """
        Load all product metadata files.

        Returns
        -------
        List[ProductMetadata]
        """

        metadata_objects = []

        yaml_files = self._discover_metadata_files()

        for yaml_file in yaml_files:

            try:
                metadata_object = self._build_metadata_object(
                    yaml_file
                )

                metadata_objects.append(metadata_object)

            except Exception as e:
                logger.error(f"Failed to load metadata: {yaml_file}")
                logger.error(f"Reason: {e}")

        return metadata_objects

    # -----------------------------------------------------

    def _discover_metadata_files(self) -> List[Path]:
        """
        Discover all product.yaml files recursively.
        """

        return sorted(
            self.kb_root.rglob(self.METADATA_FILENAME)
        )

    # -----------------------------------------------------

    def _build_metadata_object(
        self,
        yaml_file: Path
    ) -> ProductMetadata:
        """
        Build ProductMetadata object from YAML file.
        """

        metadata = self._read_yaml(yaml_file)

        category, product_id = self._extract_path_metadata(
            yaml_file
        )

        return ProductMetadata(
            product_id=product_id,
            category=category,
            path=yaml_file,
            metadata=metadata,
        )

    # -----------------------------------------------------

    def _read_yaml(
        self,
        yaml_file: Path
    ) -> Dict[str, Any]:
        """
        Read YAML safely.
        """

        with open(
            yaml_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = yaml.safe_load(f)

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError(
                f"YAML root must be a dictionary: {yaml_file}"
            )

        return data

    # -----------------------------------------------------

    def _extract_path_metadata(
        self,
        yaml_file: Path
    ):
        """
        Extract category and product_id from filesystem.

        Expected structure:
        -------------------

        knowledge_base/
        └── catalog/
            └── products/
                └── honey/
                    └── sundarbans_kholisha_honey/
                        └── product.yaml

        Extracted:
        ----------
        category   -> honey
        product_id -> sundarbans_kholisha
        """

        relative_path = yaml_file.relative_to(
            self.kb_root
        )

        parts = relative_path.parts

        if len(parts) < 5:
            raise ValueError(
                f"Invalid KB structure for metadata file: {yaml_file}"
            )

        category = parts[2]
        product_id = parts[3]

        return category, product_id


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    loader = ProductMetadataLoader(
        kb_root="knowledge_base"
    )

    metadata_objects = loader.load()

    print("\n" + "=" * 60)
    print("PRODUCT METADATA LOADER SUMMARY")
    print("=" * 60)

    print(f"Loaded metadata files: {len(metadata_objects)}")

    if metadata_objects:

        sample = metadata_objects[0]

        print("\nSample Metadata")
        print("-" * 60)

        print(f"Product ID : {sample.product_id}")
        print(f"Category   : {sample.category}")
        print(f"Path       : {sample.path}")

        print("\nMetadata Preview:")
        print(sample.metadata)
