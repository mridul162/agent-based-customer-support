"""
markdown_parser.py

Purpose:
--------
Parse markdown knowledge-base documents into structured
semantic sections while preserving retrieval-relevant structure.

Current Parser Responsibilities:
--------------------------------
- Parse markdown headings
- Preserve heading hierarchy
- Detect HTML <section> tags
- Preserve HTML/markdown tables
- Preserve semantic section boundaries
- Generate ParsedSection objects

This parser DOES NOT:
---------------------
- chunk text
- normalize text
- generate embeddings
- flatten tables
- tokenize content

Those belong to later ingestion stages.

Architecture Philosophy:
------------------------
Preserve semantic structure first.
Optimize later.
"""

import re
import sys

sys.stdout.reconfigure(encoding="utf-8") #type: ignore

from dataclasses import dataclass
from typing import List, Optional

# ---------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------

@dataclass
class ParsedSection:
    """
    Represents a semantically parsed section.
    """

    heading: str
    level: int
    content: str
    heading_path: List[str]
    section_id: Optional[str] = None


# ---------------------------------------------------------
# MARKDOWN PARSER
# ---------------------------------------------------------

class MarkdownParser:
    """
    Semantic markdown parser for Hasanah Mart KB.
    """

    HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.*)$",
        re.MULTILINE
    )

    # -----------------------------------------------------

    def parse(
        self,
        markdown_text: str
    ) -> List[ParsedSection]:
        """
        Parse markdown document into semantic sections.
        """

        # ---------------------------------------------
        # First extract HTML sections if present
        # ---------------------------------------------

        html_sections = self._extract_html_sections(
            markdown_text
        )

        # ---------------------------------------------
        # If HTML sections exist, parse them
        # ---------------------------------------------

        if html_sections:

            parsed_sections = []

            for section_id, section_content in html_sections:

                sections = self._parse_markdown_sections(
                    section_content,
                    section_id=section_id,
                )

                parsed_sections.extend(sections)

            return parsed_sections

        # ---------------------------------------------
        # Otherwise parse normally
        # ---------------------------------------------

        return self._parse_markdown_sections(
            markdown_text
        )

    # -----------------------------------------------------

    def _extract_html_sections(
        self,
        markdown_text: str
    ):
        """
        Extract semantic HTML <section> blocks.

        Example:
        --------
        <section id="our-prices">
        ...
        </section>
        """

        section_pattern = re.compile(
            r"<section(?:\s+[^>]*)?>(.*?)</section>",
            re.DOTALL | re.IGNORECASE,
        )

        id_pattern = re.compile(
            r"<section[^>]*\sid=[\"']([^\"']+)[\"'][^>]*>",
            re.IGNORECASE,
        )

        extracted_sections = []

        for match in section_pattern.finditer(markdown_text):
            opening_tag = markdown_text[
                match.start():markdown_text.find(">", match.start()) + 1
            ]

            id_match = id_pattern.search(opening_tag)

            section_id = (
                id_match.group(1)
                if id_match is not None
                else None
            )

            section_content = match.group(1)

            extracted_sections.append(
                (
                    section_id,
                    section_content,
                )
            )

        return extracted_sections

    # -----------------------------------------------------

    def _parse_markdown_sections(
        self,
        markdown_text: str,
        section_id: Optional[str] = None,
    ) -> List[ParsedSection]:
        """
        Parse markdown headings into semantic sections.
        """

        matches = list(
            self.HEADING_PATTERN.finditer(
                markdown_text
            )
        )

        if not matches:

            return [
                ParsedSection(
                    heading="Document",
                    level=1,
                    content=markdown_text.strip(),
                    heading_path=["Document"],
                    section_id=section_id,
                )
            ]

        parsed_sections = []

        heading_stack = []

        for i, match in enumerate(matches):

            # -----------------------------------------
            # Current heading
            # -----------------------------------------

            heading_marks = match.group(1)
            heading_text = match.group(2).strip()

            level = len(heading_marks)

            content_start = match.end()

            # -----------------------------------------
            # Determine section end
            # -----------------------------------------

            if i + 1 < len(matches):

                content_end = matches[i + 1].start()

            else:
                content_end = len(markdown_text)

            content = markdown_text[
                content_start:content_end
            ].strip()

            # -----------------------------------------
            # Maintain heading hierarchy
            # -----------------------------------------

            while (
                heading_stack and
                heading_stack[-1][0] >= level
            ):
                heading_stack.pop()

            heading_stack.append(
                (
                    level,
                    heading_text,
                )
            )

            heading_path = [
                item[1]
                for item in heading_stack
            ]

            # -----------------------------------------
            # Create ParsedSection
            # -----------------------------------------

            parsed_section = ParsedSection(
                heading=heading_text,
                level=level,
                content=content,
                heading_path=heading_path,
                section_id=section_id,
            )

            parsed_sections.append(
                parsed_section
            )

        return parsed_sections


# ---------------------------------------------------------
# SIMPLE TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    sample_markdown = """
# Nutrition

<section id="our-prices">

## Our Prices

<table>
<thead>
<tr>
<th>Size</th>
<th>Price</th>
</tr>
</thead>

<tbody>
<tr>
<td>250g</td>
<td>৳320</td>
</tr>
</tbody>
</table>

Prices valid as of May 2026.

</section>

## Benefits

Rich in antioxidants.
"""

    parser = MarkdownParser()

    sections = parser.parse(
        sample_markdown
    )

    print("\n" + "=" * 70)
    print("MARKDOWN PARSER OUTPUT")
    print("=" * 70)

    print(f"\nParsed Sections: {len(sections)}")

    for i, section in enumerate(sections, start=1):

        print("\n" + "-" * 70)

        print(f"SECTION #{i}")

        print("-" * 70)

        print(f"Heading     : {section.heading}")
        print(f"Level       : {section.level}")
        print(f"Section ID  : {section.section_id}")

        print("\nHeading Path:")
        print(section.heading_path)

        print("\nContent Preview:")
        print(section.content[:500])
