from bsparser.amounts import parse_amount


def test_plain_number_with_thousands_commas():
    assert parse_amount("2,002,429").value == 2002429


def test_lone_dash_is_nil_not_zero():
    amount = parse_amount("-")
    assert amount.value is None
    assert amount.kind == "nil"
