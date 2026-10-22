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


def test_section_subtotal_sums_its_items_and_reports_the_pages_rounding():
    checks = run_checks(parse_page(FIXTURE_PDF))
    prior = check_for(checks, "Total current assets", "2025-03-31")
    assert (prior.status, prior.expected, prior.printed, prior.difference, prior.bound, prior.items) == (
        "pass", 5863681, 5863684, 3, 5, 10)
    current = check_for(checks, "Total current assets", "2026-03-31")
    assert (current.difference, current.bound) == (2, 5)
