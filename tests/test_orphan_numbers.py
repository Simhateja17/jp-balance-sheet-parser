from bsparser.page import parse_lines
from bsparser.pdf_lines import Line

HEADER = [Line("（単位：百万円）", 400.0, 70.0), Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0)]
LONG = "Notes and accounts receivable - trade, and contract"


def page(body):
    return parse_lines(HEADER + [Line("Assets", 60.0, 120.0), Line("Current assets", 72.0, 134.0),
                                 Line("Cash and deposits", 84.0, 148.0, ["100", "100"])] + body)


def test_numbers_sitting_between_the_two_lines_of_a_wrapped_label_are_attached_to_the_label():
    p = page([Line(LONG, 84.0, 162.0), Line("", 400.0, 168.0, ["500", "600"]), Line("assets", 84.0, 174.0),
              Line("Inventories", 84.0, 188.0, ["70", "80"]), Line("Total current assets", 84.0, 202.0, ["670", "780"])])
    merged = [r for r in p.rows if r.label == LONG + " assets"]
    assert len(merged) == 1 and [a.value for a in merged[0].values] == [500, 600] and merged[0].role == "item"
    assert [(i.kind, i.row_id) for i in p.issues] == [("wrapped_label_merged", merged[0].id)]  # no ignored_line left
    assert not [r for r in p.rows if r.label in (LONG, "assets")]  # the two halves are not separate empty headers


def test_numbers_just_below_a_single_label_line_are_attached_to_it():
    p = page([Line("Long label with its numbers a little lower", 84.0, 162.0), Line("", 400.0, 168.0, ["500", "600"]),
              Line("Inventories", 84.0, 188.0, ["70", "80"]), Line("Total current assets", 84.0, 202.0, ["670", "780"])])
    row = [r for r in p.rows if r.label == "Long label with its numbers a little lower"][0]
    assert [a.value for a in row.values] == [500, 600]
    assert [i.kind for i in p.issues] == ["wrapped_label_merged"]


def test_a_real_page_number_keeps_its_wording_and_other_stray_numbers_say_they_were_not_attached():
    pn = page([Line("Inventories", 84.0, 162.0, ["70", "80"]), Line("", 285.0, 800.0, ["-", "11", "-"])])
    assert [i.kind for i in pn.issues] == ["ignored_line"] and "look like a page number" in pn.issues[0].message
    stray = page([Line("Inventories", 84.0, 162.0, ["70", "80"]), Line("", 400.0, 300.0, ["149,127", "156,326"])])
    assert [i.kind for i in stray.issues] == ["ignored_line"]
    assert "not attached to any row" in stray.issues[0].message and "149,127" in stray.issues[0].message
    assert "page number" not in stray.issues[0].message
