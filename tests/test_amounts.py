from bsparser.amounts import parse_amount


def test_plain_number_with_thousands_commas():
    assert parse_amount("2,002,429").value == 2002429


def test_lone_dash_is_nil_not_zero():
    amount = parse_amount("-")
    assert amount.value is None
    assert amount.kind == "nil"


def test_dash_before_digits_is_negative_not_nil():
    amount = parse_amount("-1,234")
    assert amount.value == -1234
    assert amount.kind == "value"


def test_parentheses_are_negative():
    assert parse_amount("(1,234)").value == -1234


def test_em_dash_and_fullwidth_dash_are_nil():
    for mark in ("\u2014", "\uff0d"):
        amount = parse_amount(mark)
        assert amount.value is None, mark
        assert amount.kind == "nil", mark


def test_triangle_is_negative_and_triangle_zero_is_zero_not_nil():
    assert parse_amount("△1,923,585").value == -1923585
    zero = parse_amount("△0")
    assert zero.value == 0
    assert zero.kind == "value"


def test_garbage_is_unreadable_and_keeps_raw_text():
    amount = parse_amount("1,2x4")
    assert amount.value is None
    assert amount.kind == "unreadable"
    assert amount.raw == "1,2x4"
