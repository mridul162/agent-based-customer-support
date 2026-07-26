"""
kb_validator.py

Purpose:
--------
Validate the Hasanah Mart knowledge base before ingestion.

Responsibilities:
-----------------
- Validate KB folder structure
- Validate required files
- Validate product metadata fields
- Detect duplicate product IDs
- Detect missing markdown documents
- Generate validation reports

This validator DOES NOT:
------------------------
- modify files
- auto-fix errors
- parse markdown semantics
- validate embeddings
- validate chunk quality

Those belong to later stages.
"""

import sys
sys.stdout.reconfigure(encoding="utf-8") #type: ignore

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

import yaml


# ---------------------------------------------------------
# VALIDATION DATA MODELS
# ---------------------------------------------------------

@dataclass
class ValidationIssue:
    """
    Represents a single validation issue.
    """

    severity: str   # INFO | WARNING | ERROR
    product_id: str
    message: str
    path: Path


@dataclass
class ValidationReport:
    """
    Full KB validation report.
    """

    valid: bool
    total_products: int

    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    infos: List[ValidationIssue] = field(default_factory=list)


# ---------------------------------------------------------
# KB VALIDATOR
# ---------------------------------------------------------

class KBValidator:
    """
    Knowledge base validator for Hasanah Mart RAG ingestion.
    """

    REQUIRED_MARKDOWN_FILES = {
        "overview.md",
    }

    REQUIRED_METADATA_FIELDS = {
        "schema_version",
        "product_id",
        "name",
        "category",
        "languages_supported",
        "retrieval",
    }

    def __init__(self, kb_root: str):

        self.kb_root = Path(kb_root)

        if not self.kb_root.exists():
            raise FileNotFoundError(
                f"Knowledge base path does not exist: {self.kb_root}"
            )

        self.errors = []
        self.warnings = []
        self.infos = []

        self.seen_product_ids: Set[str] = set()

    # -----------------------------------------------------

    def validate(self) -> ValidationReport:
        """
        Run full KB validation.
        """

        product_dirs = self._discover_product_directories()

        for product_dir in product_dirs:

            self._validate_product_directory(
                product_dir
            )

        valid = len(self.errors) == 0

        return ValidationReport(
            valid=valid,
            total_products=len(product_dirs),
            errors=self.errors,
            warnings=self.warnings,
            infos=self.infos,
        )

    # -----------------------------------------------------

    def _discover_product_directories(self) -> List[Path]:
        """
        Discover all product directories containing product.yaml
        """

        return [
            path.parent
            for path in self.kb_root.rglob("product.yaml")
        ]

    # -----------------------------------------------------

    def _validate_product_directory(
        self,
        product_dir: Path
    ):

        metadata_path = product_dir / "product.yaml"

        product_id = product_dir.name

        # -------------------------------------------------
        # Validate metadata existence
        # -------------------------------------------------

        if not metadata_path.exists():

            self._add_error(
                product_id,
                "Missing product.yaml",
                metadata_path,
            )

            return

        # -------------------------------------------------
        # Load metadata safely
        # -------------------------------------------------

        try:

            metadata = self._load_yaml(
                metadata_path
            )

        except Exception as e:

            self._add_error(
                product_id,
                f"Invalid YAML: {e}",
                metadata_path,
            )

            return

        # -------------------------------------------------
        # Validate required metadata fields
        # -------------------------------------------------

        self._validate_required_metadata_fields(
            product_id,
            metadata,
            metadata_path,
        )

        # -------------------------------------------------
        # Validate duplicate product IDs
        # -------------------------------------------------

        metadata_product_id = metadata.get(
            "product_id"
        )

        if metadata_product_id:

            if metadata_product_id in self.seen_product_ids:

                self._add_error(
                    product_id,
                    f"Duplicate product_id: {metadata_product_id}",
                    metadata_path,
                )

            else:
                self.seen_product_ids.add(
                    metadata_product_id
                )

        # -------------------------------------------------
        # Validate required markdown files
        # -------------------------------------------------

        self._validate_required_markdown_files(
            product_id,
            product_dir,
        )

        # -------------------------------------------------
        # Validate metadata consistency
        # -------------------------------------------------

        self._validate_metadata_consistency(
            product_id,
            metadata,
            product_dir,
            metadata_path,
        )

    # -----------------------------------------------------

    def _load_yaml(
        self,
        yaml_path: Path
    ) -> Dict:

        with open(
            yaml_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = yaml.safe_load(f)

        if data is None:
            return {}

        if not isinstance(data, dict):

            raise ValueError(
                "YAML root must be a dictionary"
            )

        return data

    # -----------------------------------------------------

    def _validate_required_metadata_fields(
        self,
        product_id: str,
        metadata: Dict,
        metadata_path: Path,
    ):

        for field in self.REQUIRED_METADATA_FIELDS:

            if field not in metadata:

                self._add_error(
                    product_id,
                    f"Missing required metadata field: {field}",
                    metadata_path,
                )

    # -----------------------------------------------------

    def _validate_required_markdown_files(
        self,
        product_id: str,
        product_dir: Path,
    ):

        for filename in self.REQUIRED_MARKDOWN_FILES:

            file_path = product_dir / filename

            if not file_path.exists():

                self._add_warning(
                    product_id,
                    f"Missing recommended markdown file: {filename}",
                    file_path,
                )

    # -----------------------------------------------------

    def _validate_metadata_consistency(
        self,
        product_id: str,
        metadata: Dict,
        product_dir: Path,
        metadata_path: Path,
    ):

        # -------------------------------------------------
        # Validate product_id consistency
        # -------------------------------------------------

        metadata_product_id = metadata.get(
            "product_id"
        )

        if metadata_product_id:

            if metadata_product_id != product_id:

                self._add_warning(
                    product_id,
                    (
                        f"Folder name '{product_id}' "
                        f"does not match metadata product_id "
                        f"'{metadata_product_id}'"
                    ),
                    metadata_path,
                )

        # -------------------------------------------------
        # Validate category consistency
        # -------------------------------------------------

        folder_category = product_dir.parent.name

        metadata_category = metadata.get(
            "category"
        )

        if metadata_category:

            if metadata_category != folder_category:

                self._add_warning(
                    product_id,
                    (
                        f"Folder category '{folder_category}' "
                        f"does not match metadata category "
                        f"'{metadata_category}'"
                    ),
                    metadata_path,
                )

    # -----------------------------------------------------

    def _add_error(
        self,
        product_id: str,
        message: str,
        path: Path,
    ):

        self.errors.append(

            ValidationIssue(
                severity="ERROR",
                product_id=product_id,
                message=message,
                path=path,
            )
        )

    # -----------------------------------------------------

    def _add_warning(
        self,
        product_id: str,
        message: str,
        path: Path,
    ):

        self.warnings.append(

            ValidationIssue(
                severity="WARNING",
                product_id=product_id,
                message=message,
                path=path,
            )
        )

    # -----------------------------------------------------

    def _add_info(
        self,
        product_id: str,
        message: str,
        path: Path,
    ):

        self.infos.append(

            ValidationIssue(
                severity="INFO",
                product_id=product_id,
                message=message,
                path=path,
            )
        )


# ---------------------------------------------------------
# VALIDATION REPORT PRINTER
# ---------------------------------------------------------

def print_validation_report(
    report: ValidationReport
):

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE VALIDATION REPORT")
    print("=" * 70)

    print(f"\nValid KB         : {report.valid}")
    print(f"Total Products   : {report.total_products}")
    print(f"Errors           : {len(report.errors)}")
    print(f"Warnings         : {len(report.warnings)}")
    print(f"Infos            : {len(report.infos)}")

    # -----------------------------------------------------
    # ERRORS
    # -----------------------------------------------------

    if report.errors:

        print("\n" + "-" * 70)
        print("ERRORS")
        print("-" * 70)

        for issue in report.errors:

            print(
                f"[ERROR] "
                f"{issue.product_id} | "
                f"{issue.message}"
            )

            print(f"Path: {issue.path}")

    # -----------------------------------------------------
    # WARNINGS
    # -----------------------------------------------------

    if report.warnings:

        print("\n" + "-" * 70)
        print("WARNINGS")
        print("-" * 70)

        for issue in report.warnings:

            print(
                f"[WARNING] "
                f"{issue.product_id} | "
                f"{issue.message}"
            )

            print(f"Path: {issue.path}")


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    validator = KBValidator(
        kb_root="knowledge_base"
    )

    report = validator.validate()

    print_validation_report(report)