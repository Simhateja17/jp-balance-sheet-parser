from pathlib import Path

from bsparser.amounts import Amount
from bsparser.checks import run_checks
from bsparser.page import parse_lines, parse_page
from bsparser.pdf_lines import Line
from bsparser.status import page_status

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def small_page(total_prior="602", total_current="603", other=("300", "300")):
    return parse_lines([
        Line("(in thousands of yen)", 400.0, 70.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Current assets", 72.0, 134.0),
        Line("Cash", 84.0, 148.0, ["100", "100"]),
        Line("Notes receivable", 84.0, 162.0, ["200", "200"]),
        Line("Other", 84.0, 176.0, list(other)),
        Line("Total current assets", 84.0, 190.0, [total_prior, total_current]),
    ])


def test_clean_fixture_page_is_ok():
    page = parse_page(FIXTURE_PDF)
    assert page_status(page, run_checks(page)) == "ok"


def test_failed_check_makes_the_page_failed():
    page = small_page("602", "603")  # 3 items: bound 2, so 603 vs 600 fails
    assert page_status(page, run_checks(page)) == "failed"


def test_unreadable_outranks_failed_and_both_issues_are_listed():
    # 2025: Other is garbled, so that check is skipped. 2026: 603 vs 600 with bound 2, so it fails.
    page = small_page("602", "603", other=("3,0x0", "300"))
    checks = run_checks(page)
    assert sorted(c.status for c in checks) == ["failed", "skipped"]
    assert [i.kind for i in page.issues] == ["unreadable_value"]
    assert page_status(page, checks) == "unreadable"
