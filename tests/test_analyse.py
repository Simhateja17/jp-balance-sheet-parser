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
