import copy
from pathlib import Path

from bsparser.arbitrate import arbitrate
from bsparser.output import build_output

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def break_a_total(output):
    """A copy where one printed total is far off, so a check fails and the page is failed."""
    broken = copy.deepcopy(output)
    for r in broken["records"]:
        if r["label"] == "Total current assets" and r["period"] == "2026-03-31":
            r["value"] += 100
    for c in broken["checks"]:
        if c["label"] == "Total current assets" and c["period"] == "2026-03-31":
            c["difference"] += 100
            c["status"] = "failed"
    broken["status"] = "failed"
    return broken


def test_the_output_with_fewer_failed_checks_wins_and_the_choice_is_recorded():
    good = build_output(FIXTURE_PDF)
    bad = break_a_total(good)
    chosen = arbitrate(text=bad, vision=good)
    assert chosen["extractor"] == "vision" and chosen["status"] == "ok"
    assert chosen["alternative"]["extractor"] == "text"  # both outputs are kept
    assert [i["kind"] for i in chosen["issues"]] == ["extractor_chosen"]
    assert "vision" in chosen["issues"][0]["message"] and "failed" in chosen["issues"][0]["message"]


def swap_two_values(output):
    """Swap two rows' 2026 numbers in one section: every sum still holds, so only agreement can reveal it."""
    swapped = copy.deepcopy(output)
    cash = [r for r in swapped["records"] if r["label"] == "Cash and deposits" and r["period"] == "2026-03-31"][0]
    notes = [r for r in swapped["records"] if r["label"] == "Notes receivable" and r["period"] == "2026-03-31"][0]
    for key in ("value", "raw"):
        cash[key], notes[key] = notes[key], cash[key]
    return swapped


def test_a_tie_goes_to_text_and_cells_where_the_extractors_disagree_are_flagged_even_if_both_pass():
    text = build_output(FIXTURE_PDF)
    vision = swap_two_values(text)
    assert [c["status"] for c in vision["checks"]] == [c["status"] for c in text["checks"]]  # still all pass
    chosen = arbitrate(text=text, vision=vision)
    assert chosen["extractor"] == "text" and chosen["status"] == "ok"
    assert len(chosen["disagreements"]) == 2
    cash = [r for r in chosen["records"] if r["label"] == "Cash and deposits" and r["period"] == "2026-03-31"][0]
    assert cash["warnings"] == ["extractors_disagree: text 608,281 vs vision 26,333"]
    agreed = [r for r in chosen["records"] if r["label"] == "Land" and r["period"] == "2026-03-31"][0]
    assert agreed["warnings"] == []


def test_when_both_fail_the_text_output_is_returned_as_failed_with_vision_attached():
    good = build_output(FIXTURE_PDF)
    text = break_a_total(good)
    for c in text["checks"]:
        if c["label"] == "Total assets" and c["period"] == "2026-03-31":
            c["status"] = "failed"  # text has two failed checks
    vision = break_a_total(good)  # vision has one: better than text, but both fail
    chosen = arbitrate(text=text, vision=vision)
    assert chosen["extractor"] == "text" and chosen["status"] == "failed"
    assert chosen["alternative"]["extractor"] == "vision"
    assert "both failed" in chosen["issues"][-1]["message"]
