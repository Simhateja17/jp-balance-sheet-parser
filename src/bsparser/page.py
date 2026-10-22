import re
from dataclasses import dataclass, field
from typing import List, Optional

from bsparser.amounts import Amount, parse_amount
from bsparser.levels import assign_levels
from bsparser.pdf_lines import Line, extract_lines
from bsparser.periods import find_periods, find_unsupported_eras
from bsparser.units import find_unit
from bsparser.roles import classify_role
from bsparser.wrapped import TIGHT_RATIO, LineInfo, find_possible_wrapped

LEVEL_TOLERANCE = 2.0  # points


@dataclass
class Row:
    id: str
    label: str
    level: int
    role: str
    path: List[str]
    parent: Optional[str] = None
    values: List[Amount] = field(default_factory=list)


@dataclass
class Issue:
    kind: str
    row_id: str
    message: str


@dataclass
class Page:
    rows: List[Row] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    periods: List[str] = field(default_factory=list)
    unit: Optional[str] = None
    unit_raw: str = ""


NET_SUFFIXES = ("\uff08\u7d14\u984d\uff09", ", net")  # （純額）, ", net"


def _is_gross_plus_net(gross_label: str, net_label: str) -> bool:
    return any(net_label == gross_label + suffix for suffix in NET_SUFFIXES)


def _split_header(lines: List[Line]):
    """Rows start below the last header line that carries two or more period dates."""
    start = 0
    for i, line in enumerate(lines):
        if len(find_periods(line.label)) + len(find_unsupported_eras(line.label)) >= 2:
            start = i + 1
    return lines[:start], lines[start:]


def _join(first: str, second: str) -> str:
    cjk = re.compile("[\u3040-\u30ff\u3400-\u9fff]")
    return first + second if cjk.search(first[-1:]) or cjk.search(second[:1]) else f"{first} {second}"


def _merge_wrapped(lines: List[Line]):
    """Merge a no-value line with the next line when both signals agree: much tighter spacing than usual,
    the same level or deeper, and the next line carries the values. Returns (lines, merged line positions)."""
    gaps = sorted(b.top - a.top for a, b in zip(lines, lines[1:]))
    usual = gaps[len(gaps) // 2] if gaps else 0.0
    merged_lines: List[Line] = []
    merged_at: List[int] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if (nxt is not None and not line.amounts and nxt.amounts
                and nxt.top - line.top < TIGHT_RATIO * usual and nxt.x0 >= line.x0 - LEVEL_TOLERANCE):
            merged_at.append(len(merged_lines))
            merged_lines.append(Line(_join(line.label, nxt.label), line.x0, line.top, nxt.amounts))
            i += 2
        else:
            merged_lines.append(line)
            i += 1
    return merged_lines, merged_at


def build_page(lines: List[Line]) -> Page:
    lines, merged_at = _merge_wrapped(lines)
    levels = assign_levels([line.x0 for line in lines], LEVEL_TOLERANCE)
    rows: List[Row] = []
    issues: List[Issue] = []
    stack: List[Row] = []  # nearest preceding row at each shallower level
    for n, (line, level) in enumerate(zip(lines, levels), start=1):
        while stack and stack[-1].level >= level:
            stack.pop()
        role = classify_role(line.label, has_values=bool(line.amounts), level=level)
        row = Row(id=f"r{n}", label=line.label, level=level, role=role, path=[r.label for r in stack],
                  values=[parse_amount(a) for a in line.amounts])
        if role in ("contra", "net") and stack:
            gross = stack[-1]
            if role == "net" and not _is_gross_plus_net(gross.label, row.label):
                issues.append(Issue("net_label_mismatch", row.id,
                                    f"net label {row.label!r} is not {gross.label!r} plus a net suffix; not linked"))
            else:
                row.parent = gross.id
        rows.append(row)
        stack.append(row)
    infos = [LineInfo(r.label, bool(r.values), r.level, line.top) for r, line in zip(rows, lines)]
    for flag in find_possible_wrapped(infos):
        issues.append(Issue("possible_wrapped_label", rows[flag.index].id,
                            f"{rows[flag.index].label!r}: {flag.reason}; not merged"))
    for position in merged_at:
        issues.append(Issue("wrapped_label_merged", rows[position].id,
                            f"label {rows[position].label!r} was wrapped over two lines and merged"))
    return Page(rows=rows, issues=issues)


def parse_page(pdf_path) -> Page:
    return parse_lines(extract_lines(pdf_path))


def parse_lines(lines: List[Line]) -> Page:
    header, table = _split_header(lines)
    ignored = [line for line in table if not line.label]
    page = build_page([line for line in table if line.label])
    for line in ignored:
        page.issues.append(Issue("ignored_line", "", f"line without a label ignored (page number?): amounts {line.amounts}"))
    header_text = " ".join(line.label for line in header)
    page.periods = find_periods(header_text)
    for era_date in find_unsupported_eras(header_text):
        page.issues.append(Issue("unsupported_era", "", f"{era_date}: only Reiwa dates are converted; no period assumed"))
    found = find_unit(header_text)
    if found:
        page.unit, page.unit_raw = found
    else:
        page.issues.append(Issue("unit_missing", "", "no known unit found in the header; none assumed"))
    for row in page.rows:
        for amount in row.values:
            if amount.kind == "unreadable":
                page.issues.append(Issue("unreadable_value", row.id, f"could not parse {amount.raw!r}; kept as raw text"))
    for row in page.rows:
        if row.values and len(row.values) != len(page.periods):
            page.issues.append(Issue(
                "column_count_mismatch", row.id,
                f"{len(row.values)} values but {len(page.periods)} period columns; none assigned by guess"))
    return page
