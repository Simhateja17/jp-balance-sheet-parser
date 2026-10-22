import re
from dataclasses import dataclass, field
from typing import List

from bsparser.levels import assign_levels
from bsparser.pdf_lines import Line, extract_lines
from bsparser.roles import classify_role

YEAR = re.compile(r"(?:19|20)\d{2}")
LEVEL_TOLERANCE = 2.0  # points


@dataclass
class Row:
    label: str
    level: int
    role: str
    path: List[str]


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


def build_rows(lines: List[Line]) -> List[Row]:
    levels = assign_levels([line.x0 for line in lines], LEVEL_TOLERANCE)
    rows: List[Row] = []
    stack: List[Row] = []  # nearest preceding row at each shallower level
    for line, level in zip(lines, levels):
        while stack and stack[-1].level >= level:
            stack.pop()
        role = classify_role(line.label, has_values=bool(line.amounts), level=level)
        row = Row(label=line.label, level=level, role=role, path=[r.label for r in stack])
        rows.append(row)
        stack.append(row)
    return rows


def parse_page(pdf_path) -> Page:
    return Page(rows=build_rows(_table_lines(extract_lines(pdf_path))))
