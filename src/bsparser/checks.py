from dataclasses import dataclass
from typing import List, Optional

from bsparser.labels import is_uchi_label
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


def bound_for(items: int, rounding: str) -> int:
    """D18. `cut`: each printed item and the total is off by less than 1 in either direction (a cut toward zero
    flips the error sign on negative lines), so |difference| <= items. `round` and `unstated`: the strict bound."""
    return items if rounding == "cut" else allowed_bound(items)


def _status(difference: int, bound: int) -> str:
    return "failed" if abs(difference) > bound else "pass"


def _wrong_width(rows, page: Page) -> str:
    """A reason when any of these rows has a different number of values than the page has period columns."""
    odd = [r for r in rows if len(r.values) != len(page.periods)]
    return "; ".join(f"row {r.id} has {len(r.values)} value{'s' if len(r.values) != 1 else ''} "
                     f"but {len(page.periods)} period columns" for r in odd)


def _skip_all(page: Page, row, reason: str) -> List[Check]:
    return [Check(row.label, row.id, period, None, None, None, 0, 0, "skipped", reason) for period in page.periods]


def _net_checks(page: Page, row, by_id, rounding: str) -> List[Check]:
    checks: List[Check] = []
    contra = [r for r in page.rows if r.role == "contra" and r.parent == row.parent]
    gross = by_id[row.parent]
    reason = _wrong_width([gross, row] + contra, page)
    if reason:
        return _skip_all(page, row, reason)
    for p, period in enumerate(page.periods):
        unreadable = [r for r in [gross, row] + contra if r.values[p].kind == "unreadable"]
        if unreadable:
            ids = ", ".join(r.id for r in unreadable)
            checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                f"unreadable value in {ids}"))
            continue
        printed = row.values[p].value
        if printed is None or gross.values[p].value is None:
            nil = row if printed is None else gross
            checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                f"value is nil in {nil.id}"))
            continue
        expected = gross.values[p].value + sum(c.values[p].value or 0 for c in contra)
        checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                            bound_for(2, rounding), 2, _status(printed - expected, bound_for(2, rounding))))
    return checks


def _total_checks(page: Page, row, rounding: str) -> List[Check]:
    checks: List[Check] = []
    contributors = []
    for r in page.rows:
        if r.role == "item" and r.values and r.path == row.path:
            nets = [n for n in page.rows if n.role == "net" and n.parent == r.id]
            contributors.append(nets[0] if nets else r)
        elif r.role == "contra" and r.parent is None and r.values and r.path == row.path:
            contributors.append(r)  # an aggregate contra line is an ordinary contributor (D17)
        elif (r.role == "subtotal" and len(r.path) == len(row.path) + 1
              and r.path[:len(row.path)] == row.path):
            contributors.append(r)  # a sub-section total feeds the total above it
    reason = _wrong_width(contributors + [row], page)
    if reason:
        return _skip_all(page, row, reason)
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
                            bound_for(len(amounts), rounding), len(amounts),
                            _status(printed - expected, bound_for(len(amounts), rounding))))
    return checks


def _group_checks(page: Page, row, rounding: str) -> List[Check]:
    """Q22: an item that has its own value and indented detail lines directly below it equals the sum of them."""
    children = [r for r in page.rows if r.role == "item" and r.values and r.path == row.path + [row.label]]
    if not children or any(is_uchi_label(c.label) for c in children):
        return []  # nothing to add up, or the detail is a partial breakdown (うち / of which)
    reason = _wrong_width(children + [row], page)
    if reason:
        return _skip_all(page, row, reason)
    checks: List[Check] = []
    for p, period in enumerate(page.periods):
        unreadable = [r for r in children + [row] if r.values[p].kind == "unreadable"]
        if unreadable:
            ids = ", ".join(r.id for r in unreadable)
            checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped", f"unreadable value in {ids}"))
            continue
        printed = row.values[p].value
        if printed is None:
            checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped", f"printed total is nil in {row.id}"))
            continue
        amounts = [c.values[p].value for c in children if c.values[p].value is not None]
        expected = sum(amounts)
        checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                            bound_for(len(amounts), rounding), len(amounts),
                            _status(printed - expected, bound_for(len(amounts), rounding))))
    return checks


def _guarded(page: Page, row, make) -> List[Check]:
    """A check that fails unexpectedly is reported as skipped with the error, so one bad row never costs the page."""
    try:
        return make()
    except Exception as exc:  # noqa: BLE001 - the point is to never crash
        return _skip_all(page, row, f"check could not run: {type(exc).__name__}: {exc}")


def run_checks(page: Page, rounding: str = "unstated") -> List[Check]:
    by_id = {r.id: r for r in page.rows}
    checks: List[Check] = []
    for row in page.rows:
        if row.role == "net" and row.parent is not None:
            checks.extend(_guarded(page, row, lambda row=row: _net_checks(page, row, by_id, rounding)))
    for row in page.rows:
        if row.role in ("subtotal", "total"):
            checks.extend(_guarded(page, row, lambda row=row: _total_checks(page, row, rounding)))
    for row in page.rows:
        if row.role == "item" and row.values:
            checks.extend(_guarded(page, row, lambda row=row: _group_checks(page, row, rounding)))
    return checks
