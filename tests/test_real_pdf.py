from pathlib import Path

from bsparser.checks import run_checks
from bsparser.page import parse_page
from bsparser.status import page_status

REAL_PDF = Path(__file__).parent.parent / "data" / "balance_sheet_after_correction.pdf"


def test_real_japanese_page_header_rows_and_clean_status():
    page = parse_page(REAL_PDF)
    assert (page.unit, page.unit_raw) == ("thousand_yen", "単位：千円")
    assert page.periods == ["2025-03-31", "2026-03-31"]
    assert len(page.rows) == 43
    assert [i.kind for i in page.issues] == ["ignored_line"]  # the printed page number "- 4 -"
    checks = run_checks(page)
    assert len(checks) == 20
    assert [c for c in checks if c.status != "pass"] == []
    assert page_status(page, checks) == "ok"
