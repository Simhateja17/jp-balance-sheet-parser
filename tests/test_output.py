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


def test_write_outputs_writes_the_json_source_of_truth_and_a_csv_view_of_the_records(tmp_path):
    import csv

    from bsparser.output import write_outputs

    json_path, csv_path = write_outputs(FIXTURE_PDF, tmp_path)
    assert json_path.name == "english_balance_sheet.json"
    assert csv_path.name == "english_balance_sheet.records.csv"
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved == build_output(FIXTURE_PDF)
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 74
    assert list(rows[0].keys())[:4] == ["id", "path", "label", "label_en"]
    assert rows[0]["path"] == "Assets / Current assets" and rows[0]["value"] == "2002429"
    nil = [r for r in rows if r["label"] == "Construction in progress"][0]
    assert (nil["value"], nil["kind"]) == ("", "nil")  # nil stays empty in CSV, never 0


def test_command_line_entry_writes_both_files_and_returns_zero(tmp_path, capsys):
    from bsparser.__main__ import main

    assert main([str(FIXTURE_PDF), str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "english_balance_sheet.json", "english_balance_sheet.records.csv"]
    assert "status: ok" in capsys.readouterr().out
