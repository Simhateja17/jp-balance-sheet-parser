import re
from dataclasses import dataclass, field
from typing import List

from bsparser.pdf_lines import Line, extract_lines

YEAR = re.compile(r"(?:19|20)\d{2}")


@dataclass
class Row:
    label: str


@dataclass
class Page:
    rows: List[Row] = field(default_factory=list)


def _table_lines(lines: List[Line]) -> List[Line]:
    """Rows start below the last header line that carries two or more years."""
    start = 0
    for i, line in enumerate(lines):
        if len(YEAR.findall(line.label)) >= 2:
            start = i + 1
    return lines[start:]


def parse_page(pdf_path) -> Page:
    return Page(rows=[Row(label=line.label) for line in _table_lines(extract_lines(pdf_path))])
