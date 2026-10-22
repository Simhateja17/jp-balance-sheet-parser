from typing import List

from bsparser.checks import Check
from bsparser.page import Page

# D6/D9: the page status is the worst issue. unreadable over failed over ok.
UNREADABLE_ISSUES = {"unreadable_value", "unit_missing", "column_count_mismatch", "unsupported_era"}
FAILED_ISSUES = {"net_label_mismatch"}


def page_status(page: Page, checks: List[Check]) -> str:
    if any(i.kind in UNREADABLE_ISSUES for i in page.issues):
        return "unreadable"
    if any(c.status == "failed" for c in checks) or any(i.kind in FAILED_ISSUES for i in page.issues):
        return "failed"
    return "ok"
