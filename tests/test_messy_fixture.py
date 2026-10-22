from pathlib import Path

from bsparser.page import parse_page

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"
CLEAN = parse_page(FIXTURES / "english_balance_sheet.pdf")


def test_messy_layout_gives_the_same_structure_and_values_as_the_clean_one_with_one_merge_flag():
    messy = parse_page(FIXTURES / "english_balance_sheet_messy.pdf")
    assert [r.label for r in messy.rows] == [r.label for r in CLEAN.rows]
    assert [r.role for r in messy.rows] == [r.role for r in CLEAN.rows]
    assert [r.level for r in messy.rows] == [r.level for r in CLEAN.rows]
    assert [r.parent for r in messy.rows] == [r.parent for r in CLEAN.rows]
    assert [[(a.value, a.kind) for a in r.values] for r in messy.rows] == [
        [(a.value, a.kind) for a in r.values] for r in CLEAN.rows]
    assert messy.periods == CLEAN.periods and messy.unit == CLEAN.unit
    merged = [r for r in messy.rows if r.label == "Electronically recorded monetary claims"][0]
    assert [(i.kind, i.row_id) for i in messy.issues] == [("wrapped_label_merged", merged.id)]
