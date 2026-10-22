import re
from dataclasses import dataclass, field
from typing import List, Optional

from bsparser.levels import assign_levels
from bsparser.pdf_lines import Line, extract_lines
from bsparser.roles import classify_role

YEAR = re.compile(r"(?:19|20)\d{2}")
LEVEL_TOLERANCE = 2.0  # points


@dataclass
class Row:
    id: str
    label: str
    level: int
    role: str
    path: List[str]
    parent: Optional[str] = None


@dataclass
class Issue:
    kind: str
    row_id: str
    message: str


@dataclass
class Page:
    rows: List[Row] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)


NET_SUFFIXES = ("\uff08\u7d14\u984d\uff09", ", net")  # （純額）, ", net"


def _is_gross_plus_net(gross_label: str, net_label: str) -> bool:
    return any(net_label == gross_label + suffix for suffix in NET_SUFFIXES)


def _table_lines(lines: List[Line]) -> List[Line]:
    """Rows start below the last header line that carries two or more years."""
    start = 0
    for i, line in enumerate(lines):
        if len(YEAR.findall(line.label)) >= 2:
            start = i + 1
    return lines[start:]


def build_page(lines: List[Line]) -> Page:
    levels = assign_levels([line.x0 for line in lines], LEVEL_TOLERANCE)
    rows: List[Row] = []
    issues: List[Issue] = []
    stack: List[Row] = []  # nearest preceding row at each shallower level
    for n, (line, level) in enumerate(zip(lines, levels), start=1):
        while stack and stack[-1].level >= level:
            stack.pop()
        role = classify_role(line.label, has_values=bool(line.amounts), level=level)
        row = Row(id=f"r{n}", label=line.label, level=level, role=role, path=[r.label for r in stack])
        if role in ("contra", "net") and stack:
            gross = stack[-1]
            if role == "net" and not _is_gross_plus_net(gross.label, row.label):
                issues.append(Issue("net_label_mismatch", row.id,
                                    f"net label {row.label!r} is not {gross.label!r} plus a net suffix; not linked"))
            else:
                row.parent = gross.id
        rows.append(row)
        stack.append(row)
    return Page(rows=rows, issues=issues)


def parse_page(pdf_path) -> Page:
    return build_page(_table_lines(extract_lines(pdf_path)))
