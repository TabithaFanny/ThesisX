import re
from typing import List, Tuple


class OutlineParser:
    """Extract headings from Markdown to build an outline."""

    @staticmethod
    def parse(text: str) -> List[Tuple[int, str, int]]:
        """Parse headings from markdown text.

        Returns list of (level, title, line_number) tuples.
        """
        results = []
        in_code_block = False

        for line_num, line in enumerate(text.split("\n"), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                # Remove trailing # marks
                title = re.sub(r"\s+#+\s*$", "", title)
                results.append((level, title, line_num))

        return results
