import json
from pathlib import Path

from bsparser.output import build_output

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def test_output_has_status_unit_periods_rows_records_checks_and_issues_and_serialises():
    out = build_output(FIXTURE_PDF)
    assert out["status"] == "ok"
    assert (out["unit"], out["unit_raw"]) == ("thousand_yen", "in thousands of yen")
    assert out["periods"] == ["2025-03-31", "2026-03-31"]
    assert (len(out["rows"]), len(out["records"]), len(out["checks"])) == (43, 74, 20)
    assert out["issues"] == []
    assert out["rows"][16] == {
        "id": "r17", "label": "Accumulated depreciation", "label_en": "Accumulated depreciation",
        "label_en_source": "original", "role": "contra", "level": 4, "parent": "r16",
        "path": ["Assets", "Non-current assets", "Property, plant and equipment", "Buildings and structures"],
    }
    assert json.loads(json.dumps(out, ensure_ascii=False)) == out
