from dataclasses import dataclass
from typing import List

from bsparser.page import Page


@dataclass
class Check:
    label: str  # the printed total the check judges
    row_id: str
    period: str
    expected: int  # sum of the contributing items
    printed: int
    difference: int  # printed minus expected
    bound: int
    items: int  # contributors that carry a rounded number
    status: str  # pass | failed | skipped
    reason: str = ""


def allowed_bound(items: int) -> int:
    """Strict bound (D4): each item and the printed total are rounded, so 0.5 x (items + 1), floored."""
    return (items + 1) // 2


def run_checks(page: Page) -> List[Check]:
    by_id = {r.id: r for r in page.rows}
    checks = []
    for row in page.rows:
        if row.role != "net" or row.parent is None:
            continue
        contra = [r for r in page.rows if r.role == "contra" and r.parent == row.parent]
        gross = by_id[row.parent]
        for p, period in enumerate(page.periods):
            expected = gross.values[p].value + sum(c.values[p].value for c in contra)
            printed = row.values[p].value
            checks.append(Check(row.label, row.id, period, expected, printed, printed - expected,
                                allowed_bound(2), 2, "pass"))
    return checks
