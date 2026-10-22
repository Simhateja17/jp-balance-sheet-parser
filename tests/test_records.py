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
    }]
    assert len(records) == 37 * 2  # 43 rows minus 6 headers, two periods
