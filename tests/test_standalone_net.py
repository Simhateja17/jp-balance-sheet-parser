from bsparser.checks import run_checks
from bsparser.page import parse_lines
from bsparser.pdf_lines import Line

NOTE = "printed as net, no gross shown"


def standalone_net_page():
    return parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("固定資産", 72.0, 134.0),
        Line("有形固定資産", 84.0, 148.0),
        Line("建物及び構築物（純額）", 96.0, 162.0, ["3,117", "2,964"]),
        Line("土地", 96.0, 176.0, ["231", "231"]),
        Line("リース資産（純額）", 96.0, 190.0, ["399", "365"]),
        Line("有形固定資産合計", 96.0, 204.0, ["3,747", "3,560"]),
    ])


def test_net_suffix_lines_directly_under_a_header_are_items_with_a_note_and_no_issue():
    page = standalone_net_page()
    net_lines = [r for r in page.rows if r.label.endswith("（純額）")]
    assert [r.role for r in net_lines] == ["item", "item"]
    assert [r.parent for r in net_lines] == [None, None]
    assert [r.notes for r in net_lines] == [[NOTE], [NOTE]]
    assert [r.notes for r in page.rows if not r.label.endswith("（純額）")] == [[]] * 5
    assert page.issues == []  # a normal layout, not an issue


def test_stand_alone_net_lines_count_in_the_section_subtotal():
    checks = run_checks(standalone_net_page())
    assert [(c.label, c.items, c.difference, c.status) for c in checks] == [
        ("有形固定資産合計", 3, 0, "pass"), ("有形固定資産合計", 3, 0, "pass")]
