from pathlib import Path

from bsparser.analyse import analyse, analyse_statement

HELDOUT = Path(__file__).parent.parent / "data" / "heldout"


def check_of(out, label, period):
    return [c for c in out["checks"] if c["label"] == label and c["period"] == period][0]


def test_auto_finds_the_page_and_takes_the_rounding_mode_from_the_cover_and_says_so():
    out = analyse(HELDOUT / "140120260416505142.pdf")  # 4098: cover says 百万円未満切捨て, balance sheet in 百万円
    assert out["page"] == 6 and out["pages_total"] == 14
    assert (out["rounding"], out["rounding_source"]) == ("cut", "cover_sentence")
    assert "百万円未満切捨て" in out["rounding_sentence"]
    current_assets = check_of(out, "流動資産合計", "2025-03-31")
    assert (current_assets.get("difference"), current_assets["bound"], current_assets["status"]) == (5, 7, "pass")


def test_an_explicit_choice_is_recorded_as_user_and_unit_mismatch_stays_unstated():
    chosen = analyse(HELDOUT / "140120260416505142.pdf", rounding="round")
    assert (chosen["rounding"], chosen["rounding_source"]) == ("round", "user")
    assert check_of(chosen, "流動資産合計", "2025-03-31")["status"] == "failed"  # the strict bound is 4
    mismatch = analyse(HELDOUT / "140120260514535920.pdf")  # 2452: cut-off stated in millions, sheet in thousands
    assert (mismatch["rounding"], mismatch["rounding_source"]) == ("unstated", "unstated")
    assert "million_yen" in mismatch["rounding_note"] and "thousand_yen" in mismatch["rounding_note"]


def test_the_note_on_stand_alone_net_lines_reaches_rows_and_records_without_becoming_a_warning():
    out = analyse(HELDOUT / "140120260416505142.pdf")  # 4098 prints net values only
    net_rows = [r for r in out["rows"] if r["label"].endswith("（純額）")]
    assert len(net_rows) == 4 and all(r["notes"] == ["printed as net, no gross shown"] for r in net_rows)
    assert all(r["role"] == "item" and r["parent"] is None for r in net_rows)
    records = [r for r in out["records"] if r["label"].endswith("（純額）")]
    assert len(records) == 8
    assert all(r["notes"] == ["printed as net, no gross shown"] and r["warnings"] == [] for r in records)
    assert [r["notes"] for r in out["records"] if not r["label"].endswith("（純額）")][0] == []
    assert out["issues"] == [i for i in out["issues"] if i["kind"] == "ignored_line"]  # no net_label_mismatch left
    assert (out["status"], sum(c["status"] == "pass" for c in out["checks"]), len(out["checks"])) == ("ok", 10, 10)


def test_the_bank_page_goes_from_four_checks_to_eight_with_the_group_checks():
    out = analyse(HELDOUT / "tanshin202603.pdf")
    assert (out["page"], out["rounding"], out["rounding_source"]) == (5, "cut", "cover_sentence")
    labels = [(c["label"], c["period"], c["status"]) for c in out["checks"]]
    assert len(labels) == 8 and {s for _, _, s in labels} == {"pass"}
    assert {l for l, _, _ in labels} == {"資産の部合計", "負債の部合計", "有形固定資産", "無形固定資産"}
    assert out["status"] == "ok"


def test_the_real_bank_equity_page_passes_its_subtotals_and_skips_the_total_whose_liabilities_are_elsewhere():
    out = analyse(HELDOUT / "tanshin202603.pdf", page=6)
    by = {(c["label"], c["period"]): c for c in out["checks"]}
    for label in ("株主資本合計", "その他の包括利益累計額合計", "純資産の部合計"):
        assert by[(label, "2025-03-31")]["status"] == "pass" and by[(label, "2026-03-31")]["status"] == "pass", label
    skipped = by[("負債及び純資産の部合計", "2025-03-31")]
    assert skipped["status"] == "skipped" and "total liabilities" in skipped["reason"]
    assert out["status"] == "ok"  # a skipped check because another page holds the piece is not a failure


def test_the_long_bar_nil_on_4224s_liabilities_page_reads_as_nil_not_as_label_text():
    out = analyse(HELDOUT / "140120260513529466.pdf", page=8)
    rows = {r["label"]: r for r in out["rows"]}
    assert "資産除去債務" in rows and "完成工事補償引当金" in rows  # the bar is no longer glued to the label
    records = {(r["label"], r["period"]): r for r in out["records"]}
    assert (records[("資産除去債務", "2025-03-31")]["kind"], records[("資産除去債務", "2025-03-31")]["value"]) == ("nil", None)
    assert records[("資産除去債務", "2026-03-31")]["value"] == 44
    assert [i["kind"] for i in out["issues"] if i["kind"] == "column_count_mismatch"] == []


import pytest


@pytest.mark.parametrize("name,page", [("140120260416505142.pdf", 11), ("140120260514535920.pdf", 10)])
def test_the_equity_statement_pages_that_used_to_crash_now_return_a_result_and_say_why_they_are_unreadable(name, page):
    out = analyse(HELDOUT / name, page=page)  # must not raise
    assert out["status"] == "unreadable"
    assert any(i["kind"] == "column_count_mismatch" for i in out["issues"])  # the matrix has more columns than periods
    assert all(c["status"] == "skipped" and c["reason"] for c in out["checks"])  # skipped with a reason, never failed


def test_the_encrypted_english_filing_is_read_without_the_page_cutting_step_that_crashed():
    fresh = Path(__file__).parent.parent / "data" / "fresh" / "vg1mvt19a00h4bsv.pdf"  # Shimadzu, AES-encrypted
    out = analyse_statement(fresh)  # used to raise PdfminerException: Invalid IV size (2) for CBC
    assert [p["page"] for p in out["pages"]][0] == 15
    assert out["pages"][0]["unit"] == "million_yen" and len(out["pages"][0]["records"]) > 20
    assert out["status"] in ("ok", "failed", "unreadable")  # a result, not a crash


def test_yokogawa_now_passes_every_check_because_its_english_cover_states_the_cut_off():
    fresh = Path(__file__).parent.parent / "data" / "fresh" / "ir_202603tanshin-en.pdf"
    out = analyse_statement(fresh)
    assert (out["rounding"], out["rounding_source"]) == ("cut", "cover_sentence")
    assert out["status"] == "ok" and [p["status"] for p in out["pages"]] == ["ok", "ok"]
    assert all(c["status"] == "pass" for c in out["cross_checks"])


def test_shimadzu_passes_once_the_numbers_printed_on_their_own_line_are_attached_to_their_labels():
    fresh = Path(__file__).parent.parent / "data" / "fresh" / "vg1mvt19a00h4bsv.pdf"
    out = analyse_statement(fresh)
    assert (out["rounding"], out["rounding_source"]) == ("cut", "cover_sentence")
    assert out["status"] == "ok" and [p["status"] for p in out["pages"]] == ["ok", "ok"]
    first = out["pages"][0]
    assert any(r["label"] == "Notes and accounts receivable - trade, and contract assets" for r in first["rows"])
    assert [i["kind"] for i in first["issues"] if i["kind"] == "wrapped_label_merged"] == ["wrapped_label_merged"]
    assert all(c["status"] == "pass" for c in out["cross_checks"])
