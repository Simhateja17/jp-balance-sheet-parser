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
