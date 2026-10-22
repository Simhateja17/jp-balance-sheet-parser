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


def synthetic_page(total_prior, total_current):
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    return parse_lines([
        Line("(in thousands of yen)", 400.0, 70.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Current assets", 72.0, 134.0),
        Line("Cash", 84.0, 148.0, ["100", "100"]),
        Line("Notes receivable", 84.0, 162.0, ["200", "200"]),
        Line("Other", 84.0, 176.0, ["300", "300"]),
        Line("Total current assets", 84.0, 190.0, [total_prior, total_current]),
    ])


def test_difference_equal_to_the_bound_passes_and_one_more_fails():
    # 3 items: strict bound is 2 (the naive 0.5-per-item rule would give 1)
    checks = run_checks(synthetic_page("602", "603"))
    on_bound = check_for(checks, "Total current assets", "2025-03-31")
    over = check_for(checks, "Total current assets", "2026-03-31")
    assert (on_bound.difference, on_bound.bound, on_bound.status) == (2, 2, "pass")
    assert (over.difference, over.bound, over.status) == (3, 2, "failed")


def test_check_with_an_unreadable_value_is_skipped_with_a_reason_not_failed():
    from bsparser.amounts import Amount

    page = synthetic_page("600", "600")
    other = [r for r in page.rows if r.label == "Other"][0]
    other.values[0] = Amount(value=None, kind="unreadable", raw="3,0x0")
    checks = run_checks(page)
    skipped = check_for(checks, "Total current assets", "2025-03-31")
    assert skipped.status == "skipped"
    assert other.id in skipped.reason and "unreadable" in skipped.reason
    assert (skipped.expected, skipped.printed, skipped.difference) == (None, None, None)
    still_checked = check_for(checks, "Total current assets", "2026-03-31")
    assert (still_checked.status, still_checked.difference) == ("pass", 0)
