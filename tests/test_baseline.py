from pathlib import Path

from bsparser.baseline import first_match
from bsparser.gold import Gold, evaluate
from bsparser.output import build_output

REAL_PDF = Path(__file__).parent.parent / "data" / "balance_sheet_after_correction.pdf"
CURRENT = ["資産の部", "流動資産"]
INTANGIBLE = ["資産の部", "固定資産", "無形固定資産"]


def test_first_match_is_right_on_a_unique_label_and_wrong_on_a_repeated_one():
    golds = [
        Gold(CURRENT, "現金及び預金", "item", "2026-03-31", "608,281"),
        Gold(CURRENT, "その他", "item", "2025-03-31", "105,260"),  # the first その他 on the page
        Gold(INTANGIBLE, "その他", "item", "2025-03-31", "10,070"),  # a later その他: first-match returns the wrong one
    ]
    baseline = first_match(REAL_PDF, golds)
    assert [r.status for r in baseline] == ["exact", "exact", "wrong_value"]
    assert [r.flagged for r in baseline] == [False, False, False]  # the baseline never warns
    parser = evaluate(build_output(REAL_PDF), golds)
    assert [r.status for r in parser] == ["exact", "exact", "exact"]
