from pathlib import Path

from bsparser.baseline import first_match
from bsparser.gold import Gold, evaluate
from bsparser.output import build_output
from bsparser.report import summarise

REAL_PDF = Path(__file__).parent.parent / "data" / "balance_sheet_after_correction.pdf"
CURRENT = ["資産の部", "流動資産"]
INTANGIBLE = ["資産の部", "固定資産", "無形固定資産"]
GOLDS = [
    Gold(CURRENT, "現金及び預金", "item", "2026-03-31", "608,281"),
    Gold(CURRENT, "その他", "item", "2025-03-31", "105,260"),
    Gold(INTANGIBLE, "その他", "item", "2025-03-31", "10,070"),
]


def test_every_slice_shows_raw_counts_next_to_the_percentage():
    out = build_output(REAL_PDF)
    table = summarise(out, GOLDS, evaluate(out, GOLDS), first_match(REAL_PDF, GOLDS))
    assert table["all"]["parser_exact"] == "3 of 3 (100%)"
    assert table["all"]["baseline_exact"] == "2 of 3 (67%)"
    assert table["repeated labels"]["parser_exact"] == "2 of 2 (100%)"  # the two その他 rows
    assert table["repeated labels"]["baseline_exact"] == "1 of 2 (50%)"
    assert table["nil and zero-with-mark"]["parser_exact"] == "0 of 0"  # no percentage on an empty slice


def test_parser_and_baseline_are_compared_on_the_value_layer_the_baseline_has_no_roles():
    out = build_output(REAL_PDF)
    golds = [
        Gold(CURRENT, "現金及び預金", "subtotal", "2026-03-31", "608,281"),  # right value, wrong role
        Gold(CURRENT, "その他", "item", "2025-03-31", "105,260"),
        Gold(INTANGIBLE, "その他", "item", "2025-03-31", "10,070"),
    ]
    table = summarise(out, golds, evaluate(out, golds), first_match(REAL_PDF, golds))
    assert table["all"]["parser_exact"] == "2 of 3 (67%)"  # value and role
    assert table["all"]["parser_value_exact"] == "3 of 3 (100%)"  # value only, like the baseline
    assert table["all"]["baseline_exact"] == "2 of 3 (67%)"  # value only
