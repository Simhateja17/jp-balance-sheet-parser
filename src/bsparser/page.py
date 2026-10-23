import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

from bsparser.amounts import Amount, parse_amount
from bsparser.labels import is_uchi_label
from bsparser.levels import assign_levels, irregular_levels
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
    notes: List[str] = field(default_factory=list)  # information, not issues (D19)


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


PAGE_NUMBER = re.compile(r"^(?:[-\u2010-\u2015\u2212]?\d{1,3}[-\u2010-\u2015\u2212]?|page\d{1,3}|p\.?\d{1,3}|\d{1,3}/\d{1,3})$", re.I)
UCHI_NOTE = "detail lines marked うち / of which are not components: no group check"
NET_ONLY_NOTE = "printed as net, no gross shown"
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
        if role == "net" and (not stack or stack[-1].role != "item"):
            row.role = "item"  # D19: nothing gross above it, so it is the only number printed for that asset
            row.notes.append(NET_ONLY_NOTE)
        elif role in ("contra", "net") and stack:
            gross = stack[-1]
            if role == "net" and not _is_gross_plus_net(gross.label, row.label):
                issues.append(Issue("net_label_mismatch", row.id,
                                    f"net label {row.label!r} is not {gross.label!r} plus a net suffix; not linked"))
            elif role == "contra" and gross.role != "item":
                pass  # one line for the whole section (D17): no single gross row, so no parent
            else:
                row.parent = gross.id
        rows.append(row)
        stack.append(row)
    for row in rows:
        detail = [r for r in rows if r.role == "item" and r.values and r.path == row.path + [row.label]]
        if row.role == "item" and row.values and any(is_uchi_label(r.label) for r in detail):
            row.notes.append(UCHI_NOTE)
    odd_levels = set(irregular_levels([line.x0 for line in lines], LEVEL_TOLERANCE))
    for row in rows:
        if row.level in odd_levels:
            issues.append(Issue("irregular_indent", row.id,
                                f"{row.label!r}: indent is far from the page's regular level step; role and path may be wrong"))
    infos = [LineInfo(r.label, bool(r.values), r.level, line.top) for r, line in zip(rows, lines)]
    for flag in find_possible_wrapped(infos):
        issues.append(Issue("possible_wrapped_label", rows[flag.index].id,
                            f"{rows[flag.index].label!r}: {flag.reason}; not merged"))
    for position in merged_at:
        issues.append(Issue("wrapped_label_merged", rows[position].id,
                            f"label {rows[position].label!r} was wrapped over two lines and merged"))
    return Page(rows=rows, issues=issues)


def parse_page(pdf_path, page: int = 1) -> Page:
    return parse_lines(extract_lines(pdf_path, page))


def _looks_like_page_number(amounts: List[str]) -> bool:
    return bool(PAGE_NUMBER.match(unicodedata.normalize("NFKC", "".join(amounts)).replace(" ", "")))


def _attach_orphan_numbers(lines: List[Line]):
    """A wrapped label can print its numbers on a line of their own, between the two label lines (a label line
    with no values, a numbers line with no label 6 points below it, the label's continuation 6 points further).
    Attach the numbers to the label (both halves joined), or to the single label line just above them. Only with
    tight spacing, and never for something that looks like a page number. Returns (lines, merged labels)."""
    gaps = sorted(b.top - a.top for a, b in zip(lines, lines[1:]))
    usual = gaps[len(gaps) // 2] if gaps else 0.0

    def tight(a: Line, b: Line) -> bool:
        return b.top - a.top < TIGHT_RATIO * usual

    out: List[Line] = []
    merged: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        after = lines[i + 2] if i + 2 < len(lines) else None
        if (line.label and not line.amounts and nxt is not None and not nxt.label and nxt.amounts
                and not _looks_like_page_number(nxt.amounts) and tight(line, nxt)):
            if (after is not None and after.label and not after.amounts and tight(nxt, after)
                    and abs(after.x0 - line.x0) <= LEVEL_TOLERANCE):
                attached = Line(_join(line.label, after.label), line.x0, line.top, nxt.amounts)
                i += 3
            else:
                attached = Line(line.label, line.x0, line.top, nxt.amounts)
                i += 2
            out.append(attached)
            merged.append(attached.label)
            continue
        out.append(line)
        i += 1
    return out, merged


def parse_lines(lines: List[Line]) -> Page:
    header, table = _split_header(lines)
    table, attached_labels = _attach_orphan_numbers(table)
    ignored = [line for line in table if not line.label]
    kept = [line for line in table if line.label]
    page_number = None
    if kept and not kept[-1].amounts and PAGE_NUMBER.match(unicodedata.normalize("NFKC", kept[-1].label).replace(" ", "")):
        page_number = kept.pop()  # D20: only the last line, only a pure page-number pattern
    page = build_page(kept)
    for label in attached_labels:
        row = next(r for r in page.rows if r.label == label)
        page.issues.append(Issue("wrapped_label_merged", row.id,
                                 f"{label!r}: its numbers were printed on a line of their own and were attached to it"))
    for line in ignored:
        if _looks_like_page_number(line.amounts):
            message = f"line without a label ignored: amounts {line.amounts} look like a page number"
        else:
            message = f"numbers without a label were not attached to any row and are left out of the table: amounts {line.amounts}"
        page.issues.append(Issue("ignored_line", "", message))
    if page_number is not None:
        page.issues.append(Issue("ignored_line", "", f"{page_number.label!r} looks like a page number and was left out"))
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
