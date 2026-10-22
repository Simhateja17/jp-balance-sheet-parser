from bsparser.amounts import parse_amount


def test_plain_number_with_thousands_commas():
    assert parse_amount("2,002,429").value == 2002429
