"""
normalizer.py

Purpose:
--------
Normalize parsed markdown content before chunking.

Responsibilities:
-----------------
- Unicode normalization
- Line ending normalization
- Whitespace stabilization
- Trailing whitespace cleanup
- Blank line stabilization
- Preserve markdown/HTML/table structure

This normalizer DOES NOT:
-------------------------
- tokenize text
- remove punctuation
- lowercase text
- transliterate Bangla
- stem words
- remove stopwords
- flatten markdown
- flatten HTML tables

Architecture Philosophy:
------------------------
Preserve semantic structure.
Reduce formatting noise.
Stabilize retrieval quality.
"""

import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

from typing import List


# ---------------------------------------------------------
# NORMALIZER
# ---------------------------------------------------------

class TextNormalizer:
    """
    Lightweight multilingual retrieval-safe normalizer.
    """

    # -----------------------------------------------------

    def normalize(
        self,
        text: str
    ) -> str:
        """
        Main normalization pipeline.
        """

        text = self._normalize_unicode(text)

        text = self._normalize_line_endings(text)

        text = self._remove_trailing_whitespace(text)

        text = self._normalize_blank_lines(text)

        text = self._normalize_horizontal_spacing(text)

        return text.strip()

    # -----------------------------------------------------

    def normalize_sections(
        self,
        sections
    ):

        for section in sections:

            section.content = self.normalize(
                section.content
            )

            section.heading = self.normalize(
                section.heading
            )

            section.heading_path = [
                self.normalize(h)
                for h in section.heading_path
            ]

        return sections

    # -----------------------------------------------------

    def _normalize_unicode(
        self,
        text: str
    ) -> str:
        """
        Normalize Unicode characters.

        Important for:
        - Bangla consistency
        - mixed Unicode inputs
        - embedding stability
        """

        return unicodedata.normalize(
            "NFKC",
            text
        )

    # -----------------------------------------------------

    def _normalize_line_endings(
        self,
        text: str
    ) -> str:
        """
        Normalize Windows/Linux/macOS line endings.
        """

        text = text.replace("\r\n", "\n")

        text = text.replace("\r", "\n")

        return text

    # -----------------------------------------------------

    def _remove_trailing_whitespace(
        self,
        text: str
    ) -> str:
        """
        Remove trailing spaces from lines.
        """

        lines = text.split("\n")

        cleaned_lines = [
            line.rstrip()
            for line in lines
        ]

        return "\n".join(cleaned_lines)

    # -----------------------------------------------------

    def _normalize_blank_lines(
        self,
        text: str
    ) -> str:
        """
        Collapse excessive blank lines.

        Preserve semantic spacing.
        """

        return re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

    # -----------------------------------------------------

    def _normalize_horizontal_spacing(
        self,
        text: str
    ) -> str:
        """
        Normalize excessive horizontal spaces.

        Important:
        ----------
        Preserve markdown tables and indentation.
        """

        normalized_lines = []

        lines = text.split("\n")

        for line in lines:

            stripped = line.strip()

            # -----------------------------------------
            # Preserve markdown tables
            # -----------------------------------------

            if stripped.startswith("|"):

                normalized_lines.append(line)

                continue

            # -----------------------------------------
            # Preserve HTML tags
            # -----------------------------------------

            if stripped.startswith("<"):

                normalized_lines.append(line)

                continue

            # -----------------------------------------
            # Normalize spaces
            # -----------------------------------------

            line = re.sub(
                r"[ \t]{2,}",
                " ",
                line
            )

            normalized_lines.append(line)

        return "\n".join(normalized_lines)


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    sample_text = """
# Nutrition\r\n\r\n\r\n


<section id="pricing">


##   Our Prices


| Size | Price |
|---|---|
| 250g | ৳320 |


</section>


This     is     a      sample      paragraph.


"""

    normalizer = TextNormalizer()

    normalized = normalizer.normalize(
        sample_text
    )

    print("\n" + "=" * 70)
    print("NORMALIZED OUTPUT")
    print("=" * 70)

    print(normalized)