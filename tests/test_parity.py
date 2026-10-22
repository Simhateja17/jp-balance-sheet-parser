from pathlib import Path

from bsparser.page import parse_page

ROOT = Path(__file__).parent.parent / "data"
JAPANESE = parse_page(ROOT / "balance_sheet_after_correction.pdf")
ENGLISH = parse_page(ROOT / "fixtures" / "english_balance_sheet.pdf")


def test_same_number_of_rows_roles_depth_and_parent_links():
    assert len(JAPANESE.rows) == len(ENGLISH.rows) == 43
    assert [r.role for r in JAPANESE.rows] == [r.role for r in ENGLISH.rows]
    assert [r.level for r in JAPANESE.rows] == [r.level for r in ENGLISH.rows]
    assert [len(r.path) for r in JAPANESE.rows] == [len(r.path) for r in ENGLISH.rows]
    assert [r.parent for r in JAPANESE.rows] == [r.parent for r in ENGLISH.rows]


def test_same_values_kinds_and_raw_structure_per_row_and_period():
    assert JAPANESE.periods == ENGLISH.periods
    assert JAPANESE.unit == ENGLISH.unit
    for jp, en in zip(JAPANESE.rows, ENGLISH.rows):
        assert [(a.value, a.kind) for a in jp.values] == [(a.value, a.kind) for a in en.values], jp.id
