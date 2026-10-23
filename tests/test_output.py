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
        "notes": [],
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


REAL_PDF = Path(__file__).parent.parent / "data" / "balance_sheet_after_correction.pdf"


def test_japanese_rows_and_records_carry_the_reviewed_translation_marked_as_such():
    out = build_output(REAL_PDF)
    cash_row = out["rows"][2]
    assert (cash_row["label"], cash_row["label_en"], cash_row["label_en_source"]) == (
        "現金及び預金", "Cash and deposits", "translation_reviewed")
    cash = [r for r in out["records"] if r["label"] == "現金及び預金" and r["period"] == "2026-03-31"][0]
    assert (cash["label_en"], cash["label_en_source"], cash["value"]) == (
        "Cash and deposits", "translation_reviewed", 608281)
    assert all(r["label_en"] for r in out["records"])  # every label on this page is in the dictionary
    english = build_output(FIXTURE_PDF)
    assert {r["label_en_source"] for r in english["records"]} == {"original"}


def test_output_records_the_rounding_mode_and_where_it_came_from():
    default = build_output(FIXTURE_PDF)
    assert (default["rounding"], default["rounding_source"]) == ("unstated", "unstated")
    assert "strict bound" in default["rounding_note"]
    chosen = build_output(FIXTURE_PDF, rounding="cut", rounding_source="user")
    assert (chosen["rounding"], chosen["rounding_source"]) == ("cut", "user")
    assert chosen["checks"][0]["bound"] == 2  # the net check: 2 items under cut (1 under round)
    hinted = build_output(FIXTURE_PDF, rounding="cut", rounding_source="cover_sentence",
                          rounding_sentence="（百万円未満切捨て）")
    assert hinted["rounding_sentence"] == "（百万円未満切捨て）"


def test_command_line_rounding_flag_defaults_to_the_cover_hint_and_records_user_choices(tmp_path, capsys):
    from bsparser.__main__ import main

    heldout = Path(__file__).parent.parent / "data" / "heldout" / "140120260416505142.pdf"
    assert main([str(heldout), str(tmp_path)]) == 0  # --rounding defaults to auto
    saved = json.loads((tmp_path / "140120260416505142.json").read_text(encoding="utf-8"))
    assert (saved["page"], saved["rounding"], saved["rounding_source"]) == (6, "cut", "cover_sentence")
    assert "rounding: cut (cover_sentence)" in capsys.readouterr().out
    assert main([str(heldout), str(tmp_path), "--rounding", "round", "--page", "6"]) == 0
    saved = json.loads((tmp_path / "140120260416505142.json").read_text(encoding="utf-8"))
    assert (saved["rounding"], saved["rounding_source"]) == ("round", "user")


def test_command_line_rejects_an_unknown_rounding_value(tmp_path):
    import pytest

    from bsparser.__main__ import main

    with pytest.raises(SystemExit) as stop:
        main([str(FIXTURE_PDF), str(tmp_path), "--rounding", "sometimes"])
    assert stop.value.code == 2
