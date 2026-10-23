from bsparser.checks import run_checks
from bsparser.page import parse_lines
from bsparser.pdf_lines import Line


def aggregate_page():
    return parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("固定資産", 72.0, 134.0),
        Line("有形固定資産", 84.0, 148.0),
        Line("建物及び構築物", 96.0, 162.0, ["1,000", "1,100"]),
        Line("機械装置及び運搬具", 96.0, 176.0, ["2,000", "2,100"]),
        Line("土地", 96.0, 190.0, ["500", "500"]),
        Line("減価償却累計額", 96.0, 204.0, ["△1,200", "△1,300"]),  # one line for the whole section
        Line("有形固定資産合計", 96.0, 218.0, ["2,300", "2,400"]),
    ])


def test_an_aggregate_contra_line_has_no_parent_and_no_issue():
    page = aggregate_page()
    contra = [r for r in page.rows if r.label == "減価償却累計額"][0]
    assert contra.role == "contra"
    assert contra.parent is None  # D2: parent is only a single gross link
    assert page.issues == []


def test_an_aggregate_contra_line_counts_in_the_section_subtotal_and_no_net_check_exists():
    checks = run_checks(aggregate_page())
    assert [c.label for c in checks] == ["有形固定資産合計", "有形固定資産合計"]  # no gross-plus-contra check
    prior, current = checks
    assert (prior.expected, prior.printed, prior.difference, prior.items, prior.status) == (2300, 2300, 0, 4, "pass")
    assert (current.expected, current.difference, current.status) == (2400, 0, "pass")
