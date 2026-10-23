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
