from pathlib import Path

from bsparser.checks import run_checks
from bsparser.page import parse_page

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def check_for(checks, label, period):
    found = [c for c in checks if c.label == label and c.period == period]
    assert len(found) == 1, (label, period, len(found))
    return found[0]


def test_net_equals_gross_plus_contra_reports_difference_and_bound():
    checks = run_checks(parse_page(FIXTURE_PDF))
    c = check_for(checks, "Buildings and structures, net", "2026-03-31")
    assert (c.status, c.difference, c.bound, c.items) == ("pass", -1, 1, 2)
