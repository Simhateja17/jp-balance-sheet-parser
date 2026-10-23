from pathlib import Path

from bsparser.page import parse_page
from bsparser.records import make_records

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def test_one_record_per_value_row_per_period_with_the_d1_fields():
    records = make_records(parse_page(FIXTURE_PDF))
    cash = [r for r in records if r["label"] == "Cash and deposits" and r["period"] == "2026-03-31"]
    assert cash == [{
        "id": "r3|2026-03-31",
        "path": ["Assets", "Current assets"],
        "label": "Cash and deposits",
        "label_en": "Cash and deposits",
        "label_en_source": "original",
        "role": "item",
        "parent": None,
        "period": "2026-03-31",
        "value": 608281,
        "kind": "value",
        "raw": "608,281",
        "unit": "thousand_yen",
        "warnings": [],
        "notes": [],
    }]
    assert len(records) == 37 * 2  # 43 rows minus 6 headers, two periods


def test_parent_links_stay_inside_the_same_period_and_nil_keeps_its_raw_text():
    records = make_records(parse_page(FIXTURE_PDF))
    by_id = {r["id"]: r for r in records}
    contra = by_id["r17|2025-03-31"]
    assert contra["label"] == "Accumulated depreciation"
    assert contra["parent"] == "r16|2025-03-31"
    assert by_id[contra["parent"]]["label"] == "Buildings and structures"
    nil = [r for r in records if r["label"] == "Construction in progress" and r["period"] == "2025-03-31"][0]
    assert (nil["value"], nil["kind"], nil["raw"]) == (None, "nil", "-")


def test_unreadable_value_record_keeps_raw_text_and_carries_a_warning():
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    page = parse_lines([
        Line("(in thousands of yen)", 400.0, 70.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Notes receivable", 72.0, 134.0, ["1,2x4", "200"]),
    ])
    bad, good = make_records(page)
    assert (bad["value"], bad["kind"], bad["raw"]) == (None, "unreadable", "1,2x4")
    assert bad["warnings"] == ["unreadable value: could not parse '1,2x4'"]
    assert good["warnings"] == []


def test_missing_translation_is_null_with_a_warning_and_does_not_change_status():
    from bsparser.checks import run_checks
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line
    from bsparser.status import page_status

    page = parse_lines([
        Line("（単位：千円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("謎の科目", 72.0, 134.0, ["100", "200"]),
    ])
    first, second = make_records(page)
    assert (first["label_en"], first["label_en_source"]) == (None, "missing")
    assert first["warnings"] == ["translation_missing"]
    assert page_status(page, run_checks(page)) == "ok"
