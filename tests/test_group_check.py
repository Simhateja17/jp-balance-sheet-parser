from bsparser.checks import run_checks
from bsparser.page import parse_lines
from bsparser.pdf_lines import Line


def bank_like(detail_label="建物"):
    return parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("貸出金", 72.0, 134.0, ["100", "100"]),
        Line("有形固定資産", 72.0, 148.0, ["55,896", "55,526"]),
        Line(detail_label, 84.0, 162.0, ["20,230", "19,563"]),
        Line("土地", 84.0, 176.0, ["30,735", "30,735"]),
        Line("建設仮勘定", 84.0, 190.0, ["131", "487"]),
        Line("その他の有形固定資産", 84.0, 204.0, ["4,798", "4,740"]),
        Line("資産の部合計", 72.0, 218.0, ["55,996", "55,626"]),
    ])


def test_a_group_line_with_its_own_value_must_equal_the_sum_of_its_detail_lines():
    checks = [c for c in run_checks(bank_like()) if c.label == "有形固定資産"]
    assert [(c.period, c.expected, c.printed, c.difference, c.items, c.bound, c.status) for c in checks] == [
        ("2025-03-31", 55894, 55896, 2, 4, 2, "pass"),
        ("2026-03-31", 55525, 55526, 1, 4, 2, "pass"),
    ]


def test_the_group_line_stays_an_item_with_no_parent_and_the_section_total_ignores_its_detail():
    page = bank_like()
    group = [r for r in page.rows if r.label == "有形固定資産"][0]
    assert (group.role, group.parent) == ("item", None)
    total = [c for c in run_checks(page) if c.label == "資産の部合計"]
    assert [(c.items, c.difference, c.status) for c in total] == [(2, 0, "pass"), (2, 0, "pass")]  # 貸出金 + 有形固定資産


def test_detail_lines_marked_uchi_or_of_which_are_not_components_so_no_group_check_and_a_note():
    for marker in ("うち建物", "（うち建物）", "(うち建物)", "of which buildings"):
        page = bank_like(detail_label=marker)
        assert [c for c in run_checks(page) if c.label == "有形固定資産"] == [], marker
        group = [r for r in page.rows if r.label == "有形固定資産"][0]
        assert group.notes == ["detail lines marked うち / of which are not components: no group check"], marker
