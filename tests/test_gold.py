from bsparser.gold import load_gold

TEMPLATE = """# Gold template
| # | path | label (as printed) | label_en (translation) | role | why tricky | raw 2025-03-31 | raw 2026-03-31 |
|---|------|--------------------|------------------------|------|------------|----------------|----------------|
| 1 | | 資産の部 | Assets | header | | | |
| 3 | 資産の部/流動資産 | 現金及び預金 | Cash and deposits | item | | 2,002,429 | 608,281 |
| 12 | 資産の部/流動資産 | 貸倒引当金 | Allowance for doubtful accounts | item | negative mark | △2,979 | △0 |
| 26 | 資産の部/固定資産/有形固定資産 | 建設仮勘定 | Construction in progress | item | printed dash | － | 4,553 |
| 30 | 資産の部/固定資産/有形固定資産 | 有形固定資産合計 | Total property | subtotal | | | |
"""


def test_only_filled_cells_become_gold_records_keyed_by_path_label_and_period(tmp_path):
    path = tmp_path / "template.md"
    path.write_text(TEMPLATE, encoding="utf-8")
    gold = load_gold(path)
    assert len(gold) == 6  # 3 rows x 2 periods; header and empty rows give none
    cash = [g for g in gold if g.label == "現金及び預金" and g.period == "2026-03-31"][0]
    assert (cash.path, cash.role, cash.raw) == (["資産の部", "流動資産"], "item", "608,281")
    zero = [g for g in gold if g.label == "貸倒引当金" and g.period == "2026-03-31"][0]
    assert zero.raw == "△0"
    nil = [g for g in gold if g.label == "建設仮勘定" and g.period == "2025-03-31"][0]
    assert nil.raw == "－"


from pathlib import Path

from bsparser.gold import Gold, evaluate
from bsparser.output import build_output

REAL_PDF = Path(__file__).parent.parent / "data" / "balance_sheet_after_correction.pdf"


def gold(label, raw, period="2026-03-31", role="item", path=("資産の部", "流動資産")):
    return Gold(list(path), label, role, period, raw)


def test_correct_value_is_exact_and_a_wrong_value_on_a_clean_page_is_a_silent_error():
    out = build_output(REAL_PDF)
    results = evaluate(out, [gold("現金及び預金", "608,281"), gold("現金及び預金", "608,282")])
    assert [r.status for r in results] == ["exact", "wrong_value"]
    assert [r.flagged for r in results] == [False, False]  # page status ok, so the wrong one is silent


def test_key_that_matches_nothing_or_several_records_is_never_a_guess():
    out = build_output(REAL_PDF)
    missing = evaluate(out, [gold("現金及び預金", "608,281", path=("資産の部", "固定資産"))])
    assert [r.status for r in missing] == ["not_found"]
    doubled = {"status": "ok", "records": [out["records"][0], out["records"][0]]}
    first = out["records"][0]
    several = evaluate(doubled, [gold(first["label"], first["raw"], first["period"], path=first["path"])])
    assert [r.status for r in several] == ["ambiguous"]


def test_structure_layer_is_separate_from_the_value_layer():
    out = build_output(REAL_PDF)
    (right_value_wrong_role,) = evaluate(out, [gold("現金及び預金", "608,281", role="subtotal")])
    assert (right_value_wrong_role.status, right_value_wrong_role.value_ok, right_value_wrong_role.role_ok) == (
        "wrong_role", True, False)
    (wrong_value_right_role,) = evaluate(out, [gold("現金及び預金", "1", role="item")])
    assert (wrong_value_right_role.status, wrong_value_right_role.value_ok, wrong_value_right_role.role_ok) == (
        "wrong_value", False, True)


def test_gold_typed_with_ascii_digits_spaces_or_a_plain_dash_still_matches_the_printed_text():
    out = build_output(REAL_PDF)
    nil_path = ("資産の部", "固定資産", "有形固定資産")
    typed_plain_dash = gold("建設仮勘定", "-", period="2025-03-31", path=nil_path)
    typed_with_spaces = gold("現金及び預金", "608, 281")
    typed_fullwidth_digits = gold("現金及び預金", "６０８，２８１")
    results = evaluate(out, [typed_plain_dash, typed_with_spaces, typed_fullwidth_digits])
    assert [r.status for r in results] == ["exact", "exact", "exact"]
    (still_wrong,) = evaluate(out, [gold("貸倒引当金", "(0)")])  # a different mark is not the same text
    assert still_wrong.status == "wrong_value"


FULL_TEMPLATE = """| # | path | label (as printed) | label_en (translation) | role | why tricky | raw 2025-03-31 | raw 2026-03-31 |
|---|------|--------------------|------------------------|------|------------|----------------|----------------|
| 1 | | 資産の部 | Assets | header | | | |
| 2 | 資産の部 | 固定資産 | Fixed assets | header | | | |
| 3 | 資産の部/固定資産 | 建物 | Buildings | item | | 1,000 | 2,000 |
| 4 | 資産の部/固定資産/建物 | 減価償却累計額 | Accumulated depreciation | contra | | △400 | △500 |
| 5 | 資産の部/固定資産/建物 | 建物（純額） | Buildings, net | net | | 600 | 1,500 |
"""


def test_gold_page_rebuilds_rows_values_and_gross_links_so_the_same_checks_can_run(tmp_path):
    from bsparser.checks import run_checks
    from bsparser.gold import gold_page

    path = tmp_path / "template.md"
    path.write_text(FULL_TEMPLATE, encoding="utf-8")
    page = gold_page(path)
    assert page.periods == ["2025-03-31", "2026-03-31"]
    assert [r.id for r in page.rows] == ["r1", "r2", "r3", "r4", "r5"]
    assert page.rows[3].parent == "r3" and page.rows[4].parent == "r3"
    assert [a.value for a in page.rows[3].values] == [-400, -500]
    checks = run_checks(page)
    assert [(c.label, c.period, c.difference, c.status) for c in checks] == [
        ("建物（純額）", "2025-03-31", 0, "pass"), ("建物（純額）", "2026-03-31", 0, "pass")]


GOLD_TEMPLATE = Path(__file__).parent.parent / "data" / "gold" / "balance_sheet_after_correction.template.md"


def test_the_real_gold_values_satisfy_the_accounting_identities_with_the_strict_bound():
    from bsparser.checks import run_checks
    from bsparser.gold import gold_page

    checks = run_checks(gold_page(GOLD_TEMPLATE))
    assert len(checks) == 20
    failing = [(c.label, c.period, c.difference, c.bound, c.status) for c in checks if c.status != "pass"]
    assert failing == []
