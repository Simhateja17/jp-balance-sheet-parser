from dataclasses import dataclass, field
from typing import List, Optional

from bsparser.labels import is_uchi_label
from bsparser.page import Page
from bsparser.totals import kind_of_total


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
    row_ids: List[str] = field(default_factory=list)  # the printed total first, then every row it adds up


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


def _tag(checks: List[Check], rows) -> List[Check]:
    ids = [r.id for r in rows]
    for c in checks:
        c.row_ids = list(ids)
    return checks


def _net_checks(page: Page, row, by_id, rounding: str) -> List[Check]:
    contra = [r for r in page.rows if r.role == "contra" and r.parent == row.parent]
    gross = by_id[row.parent]
    return _tag(_net_checks_untagged(page, row, gross, contra, rounding), [row, gross] + contra)


def _net_checks_untagged(page: Page, row, gross, contra, rounding: str) -> List[Check]:
    checks: List[Check] = []
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


def _contributors(page: Page, row):
    """What a subtotal or total adds up. Walking the section in page order: items (a net line replaces its gross),
    aggregate contra lines and sub-section totals go into the current run. A subtotal printed with no heading above
    it adds only the run since the previous subtotal. The section's last total adds the earlier subtotals plus the
    run not yet covered by one (D21 item 3)."""
    section_totals = [r for r in page.rows if r.role in ("subtotal", "total") and r.values and r.path == row.path]
    is_last = bool(section_totals) and section_totals[-1] is row
    covered, run = [], []
    for r in page.rows[:page.rows.index(row)]:
        if r in section_totals:
            covered.append(r)
            run = []
        elif r.role == "item" and r.values and r.path == row.path:
            nets = [n for n in page.rows if n.role == "net" and n.parent == r.id]
            run.append(nets[0] if nets else r)
        elif r.role == "contra" and r.parent is None and r.values and r.path == row.path:
            run.append(r)  # an aggregate contra line is an ordinary contributor (D17)
        elif r.role == "subtotal" and len(r.path) == len(row.path) + 1 and r.path[:len(row.path)] == row.path:
            run.append(r)  # a sub-section total feeds the total above it
    return covered + run if is_last else run


def _sum_of_totals(page: Page, row, parts, rounding: str) -> List[Check]:
    """A total that is the sum of other printed totals (total liabilities and net assets = liabilities + net assets)."""
    return _tag(_sum_of_totals_untagged(page, row, parts, rounding), [row] + parts)


def _sum_of_totals_untagged(page: Page, row, parts, rounding: str) -> List[Check]:
    checks: List[Check] = []
    reason = _wrong_width(parts + [row], page)
    if reason:
        return _skip_all(page, row, reason)
    for p, period in enumerate(page.periods):
        unreadable = [r for r in parts + [row] if r.values[p].kind == "unreadable"]
        nil = [r for r in parts + [row] if r.values[p].value is None and r.values[p].kind != "unreadable"]
        if unreadable or nil:
            ids = ", ".join(r.id for r in (unreadable or nil))
            checks.append(Check(row.label, row.id, period, None, None, None, 0, 0, "skipped",
                                f"{'unreadable' if unreadable else 'nil'} value in {ids}"))
            continue
        expected = sum(r.values[p].value for r in parts)
        printed = row.values[p].value
        checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                            bound_for(len(parts), rounding), len(parts),
                            _status(printed - expected, bound_for(len(parts), rounding))))
    return checks


def _la_na_checks(page: Page, row, rounding: str) -> List[Check]:
    pieces = {kind: [r for r in page.rows if r.values and kind_of_total(r.label) == kind] for kind in ("liabilities", "net_assets")}
    missing = [name for name, kind in (("liabilities", "liabilities"), ("net assets", "net_assets")) if not pieces[kind]]
    if missing:
        present = [pieces[kind][0] for kind in ("liabilities", "net_assets") if pieces[kind]]
        return _tag(_skip_all(page, row, "total " + " and total ".join(missing) + " not on this page"), [row] + present)
    return _sum_of_totals(page, row, [pieces["liabilities"][0], pieces["net_assets"][0]], rounding)


def _total_checks(page: Page, row, rounding: str) -> List[Check]:
    if kind_of_total(row.label) == "liabilities_net_assets":
        return _la_na_checks(page, row, rounding)
    contributors = _contributors(page, row)
    return _tag(_total_checks_untagged(page, row, contributors, rounding), [row] + contributors)


def _total_checks_untagged(page: Page, row, contributors, rounding: str) -> List[Check]:
    checks: List[Check] = []
    if not contributors:
        return _skip_all(page, row, "no components on this page")  # never a failure for lack of components
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
    return _tag(_group_checks_untagged(page, row, children, rounding), [row] + children)


def _group_checks_untagged(page: Page, row, children, rounding: str) -> List[Check]:
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
        return _tag(_skip_all(page, row, f"check could not run: {type(exc).__name__}: {exc}"), [row])


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
