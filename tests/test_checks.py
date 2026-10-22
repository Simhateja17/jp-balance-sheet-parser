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


def test_property_subtotal_uses_net_lines_and_sits_exactly_on_the_bound():
    checks = run_checks(parse_page(FIXTURE_PDF))
    c = check_for(checks, "Total property, plant and equipment", "2026-03-31")
    # items: buildings net, machinery net, land, lease net, construction in progress, other net
    assert (c.status, c.difference, c.bound, c.items) == ("pass", 3, 3, 6)
    prior = check_for(checks, "Total property, plant and equipment", "2025-03-31")
    # construction in progress is nil in 2025: no rounded number, so it is not counted
    assert (prior.difference, prior.bound, prior.items) == (1, 3, 5)


def test_totals_of_subtotals_current_plus_fixed_and_the_strict_bound_edge():
    checks = run_checks(parse_page(FIXTURE_PDF))
    fixed = check_for(checks, "Total non-current assets", "2025-03-31")
    # 3 subtotals, off by 2: the strict bound is 2; the naive 0.5-per-item bound would be 1
    assert (fixed.status, fixed.difference, fixed.bound, fixed.items) == ("pass", 2, 2, 3)
    total = check_for(checks, "Total assets", "2026-03-31")
    assert (total.status, total.difference, total.bound, total.items) == ("pass", 1, 1, 2)
