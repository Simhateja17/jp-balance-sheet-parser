from pathlib import Path

from bsparser.page import parse_page

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def test_parse_page_returns_the_43_table_rows_without_the_header_block():
    page = parse_page(FIXTURE_PDF)
    assert len(page.rows) == 43
    assert page.rows[0].label == "Assets"
    assert page.rows[-1].label == "Total assets"
