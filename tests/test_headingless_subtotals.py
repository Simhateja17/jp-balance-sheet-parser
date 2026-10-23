from bsparser.checks import run_checks
from bsparser.page import parse_lines
from bsparser.pdf_lines import Line

HEADER = [Line("（単位：百万円）", 400.0, 70.0), Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0)]


def equity_page():
    """The bank's net assets page: subtotals with no heading above them (2025 column; 2026 repeats it)."""
    def row(label, a, top):
        return Line(label, 73.0, top, [a, a])
    return parse_lines(HEADER + [
        Line("純資産の部", 62.0, 120.0),
        row("資本金", "49,759", 134.0), row("資本剰余金", "39,704", 148.0), row("利益剰余金", "204,450", 162.0),
        row("自己株式", "△7,889", 176.0), row("株主資本合計", "286,026", 190.0),
        row("その他有価証券評価差額金", "5,801", 204.0), row("繰延ヘッジ損益", "－", 218.0),
        row("土地再評価差額金", "6,907", 232.0), row("退職給付に係る調整累計額", "5,246", 246.0),
        row("その他の包括利益累計額合計", "17,955", 260.0),
        row("非支配株主持分", "6,742", 274.0), row("純資産の部合計", "310,724", 288.0),
    ])


def test_an_intermediate_subtotal_adds_only_the_items_since_the_previous_subtotal():
    checks = {c.label: c for c in run_checks(equity_page()) if c.period == "2025-03-31"}
    a = checks["株主資本合計"]
    assert (a.expected, a.printed, a.difference, a.items, a.status) == (286024, 286026, 2, 4, "pass")
    b = checks["その他の包括利益累計額合計"]
    # 繰延ヘッジ損益 is nil: not counted as an item (no rounding error)
    assert (b.expected, b.printed, b.difference, b.items, b.status) == (17954, 17955, 1, 3, "pass")


def test_the_final_total_adds_the_earlier_subtotals_plus_the_items_not_covered_by_one():
    c = {c.label: c for c in run_checks(equity_page()) if c.period == "2025-03-31"}["純資産の部合計"]
    assert (c.expected, c.printed, c.difference, c.items, c.status) == (310723, 310724, 1, 3, "pass")  # A + B + 非支配株主持分
