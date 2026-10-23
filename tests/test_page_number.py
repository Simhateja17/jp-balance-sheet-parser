import pytest

from bsparser.page import parse_lines
from bsparser.pdf_lines import Line


def page_with_last(label):
    return parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("流動資産", 72.0, 134.0),
        Line("現金及び預金", 84.0, 148.0, ["100", "200"]),
        Line(label, 286.0, 800.0),
    ])


@pytest.mark.parametrize("label", ["-5-", "- 5 -", "－５－", "5", "Page 5", "5/12", "p.5"])
def test_a_last_label_only_line_that_is_a_page_number_is_left_out_with_an_informational_issue(label):
    page = page_with_last(label)
    assert [r.label for r in page.rows] == ["資産の部", "流動資産", "現金及び預金"]
    assert [(i.kind, "page number" in i.message) for i in page.issues] == [("ignored_line", True)]


def test_a_line_that_only_looks_like_a_number_in_the_middle_of_the_table_is_never_dropped():
    page = parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("12", 72.0, 134.0),  # a label that looks like a number, with a row after it
        Line("現金及び預金", 84.0, 148.0, ["100", "200"]),
    ])
    assert [r.label for r in page.rows] == ["資産の部", "12", "現金及び預金"]


def test_a_last_line_that_is_not_a_page_number_stays_a_row():
    page = page_with_last("注記")
    assert [r.label for r in page.rows][-1] == "注記"
