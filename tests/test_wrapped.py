from bsparser.wrapped import LineInfo, find_possible_wrapped


def test_novalue_line_followed_by_same_level_line_with_values_is_flagged():
    lines = [
        LineInfo("Current assets", False, 1, 100.0),
        LineInfo("Allowance for doubtful accounts and other", False, 2, 114.0),
        LineInfo("long-term receivables", True, 2, 128.0),
    ]
    flagged = find_possible_wrapped(lines)
    assert [f.index for f in flagged] == [1]
    assert flagged[0].reason == "next line at the same level has values"


def test_novalue_line_with_much_tighter_spacing_to_the_next_line_is_flagged():
    lines = [
        LineInfo("Cash and deposits", True, 2, 100.0),
        LineInfo("Notes receivable", True, 2, 114.0),
        LineInfo("Investments in unconsolidated subsidiaries", False, 2, 128.0),
        LineInfo("and affiliates", True, 3, 136.0),
        LineInfo("Land", True, 2, 150.0),
        LineInfo("Buildings", True, 2, 164.0),
    ]
    flagged = find_possible_wrapped(lines)
    assert [f.index for f in flagged] == [2]
    assert flagged[0].reason == "next line is much closer than the usual line spacing"


def test_header_with_normal_spacing_and_a_deeper_next_line_is_not_flagged():
    lines = [
        LineInfo("Current assets", False, 1, 100.0),
        LineInfo("Cash and deposits", True, 2, 114.0),
        LineInfo("Notes receivable", True, 2, 128.0),
    ]
    assert find_possible_wrapped(lines) == []
