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
