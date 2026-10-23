from pathlib import Path

from bsparser.vision_eval import judge_replies

ROOT = Path(__file__).parent.parent
PDF = ROOT / "data" / "balance_sheet_after_correction.pdf"
GOLD = ROOT / "data" / "gold" / "balance_sheet_after_correction.template.md"
RUNS = [ROOT / "outputs" / f"vision_reply_japanese_run{n}.json" for n in (1, 2, 3)]


def test_saved_vision_replies_are_judged_by_the_same_checks_gold_and_text_agreement():
    text = judge_replies(PDF, GOLD, RUNS)
    run_rows = [line for line in text.splitlines() if line.startswith("| run ") and line[6].isdigit()]
    assert len(run_rows) == 3
    assert "| run 1 | ok | 20 of 20 | 74 of 74 (100%) | 0 |" in text
    assert "| run 3 | ok | 20 of 20 | 74 of 74 (100%) | 0 |" in text
    assert "—" not in text.replace("— ", "")  # style check below: no em dash used as punctuation
