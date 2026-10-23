from pathlib import Path

from bsparser.analyse import analyse

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
