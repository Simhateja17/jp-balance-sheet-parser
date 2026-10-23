from dataclasses import dataclass
from typing import List, Optional

from bsparser.page import Page


@dataclass
class Check:
    label: str  # the printed total the check judges
    row_id: str
    period: str
    expected: Optional[int]  # sum of the contributing items; None when skipped
    printed: Optional[int]
    difference: Optional[int]  # printed minus expected
    bound: int
    items: int  # contributors that carry a rounded number
    status: str  # pass | failed | skipped
    reason: str = ""


def allowed_bound(items: int) -> int:
    """Strict bound (D4): each item and the printed total are rounded, so 0.5 x (items + 1), floored."""
    return (items + 1) // 2


def _status(difference: int, bound: int) -> str:
    return "failed" if abs(difference) > bound else "pass"


def _wrong_width(rows, page: Page) -> str:
    """A reason when any of these rows has a different number of values than the page has period columns."""
    odd = [r for r in rows if len(r.values) != len(page.periods)]
    return "; ".join(f"row {r.id} has {len(r.values)} value{'s' if len(r.values) != 1 else ''} "
                     f"but {len(page.periods)} period columns" for r in odd)


def _skip_all(page: Page, row, reason: str) -> List[Check]:
    return [Check(row.label, row.id, period, None, None, None, 0, 0, "skipped", reason) for period in page.periods]


def run_checks(page: Page) -> List[Check]:
    by_id = {r.id: r for r in page.rows}
    checks = []
    for row in page.rows:
        if row.role != "net" or row.parent is None:
            continue
        contra = [r for r in page.rows if r.role == "contra" and r.parent == row.parent]
        gross = by_id[row.parent]
        reason = _wrong_width([gross, row] + contra, page)
        if reason:
            checks.extend(_skip_all(page, row, reason))
            continue
        for p, period in enumerate(page.periods):
            unreadable = [r for r in [gross, row] + contra if r.values[p].kind == "unreadable"]
            if unreadable:
                ids = ", ".join(r.id for r in unreadable)
                checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                    f"unreadable value in {ids}"))
                continue
            expected = gross.values[p].value + sum(c.values[p].value or 0 for c in contra)
            printed = row.values[p].value
            checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                                allowed_bound(2), 2,
                                _status(printed - expected, allowed_bound(2))))
    for row in page.rows:
        if row.role not in ("subtotal", "total"):
            continue
        contributors = []
        for r in page.rows:
            if r.role == "item" and r.values and r.path == row.path:
                nets = [n for n in page.rows if n.role == "net" and n.parent == r.id]
                contributors.append(nets[0] if nets else r)
            elif (r.role == "subtotal" and len(r.path) == len(row.path) + 1
                  and r.path[:len(row.path)] == row.path):
                contributors.append(r)  # a sub-section total feeds the total above it
        reason = _wrong_width(contributors + [row], page)
        if reason:
            checks.extend(_skip_all(page, row, reason))
            continue
        for p, period in enumerate(page.periods):
            unreadable = [r for r in contributors + [row] if r.values[p].kind == "unreadable"]
            if unreadable:
                ids = ", ".join(r.id for r in unreadable)
                checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                    f"unreadable value in {ids}"))
                continue
            printed = row.values[p].value
            if printed is None:
                checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                    f"printed total is nil in {row.id}"))
                continue
            amounts = [c.values[p].value for c in contributors if c.values[p].value is not None]
            expected = sum(amounts)
            checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                                allowed_bound(len(amounts)), len(amounts),
                                _status(printed - expected, allowed_bound(len(amounts)))))
    return checks
