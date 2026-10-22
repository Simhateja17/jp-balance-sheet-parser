from bsparser.units import find_unit


def test_japanese_units_yen_thousand_and_million():
    assert find_unit("（単位：千円）") == ("thousand_yen", "単位：千円")
    assert find_unit("（単位：百万円）") == ("million_yen", "単位：百万円")
    assert find_unit("（単位：円）") == ("yen", "単位：円")


def test_english_units_still_work_and_unknown_or_missing_units_are_none():
    assert find_unit("(in thousands of yen)") == ("thousand_yen", "in thousands of yen")
    assert find_unit("(in millions of yen)") == ("million_yen", "in millions of yen")
    assert find_unit("（単位：ドル）") is None
    assert find_unit("連結貸借対照表") is None
