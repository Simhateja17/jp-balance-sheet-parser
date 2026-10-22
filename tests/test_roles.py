from bsparser.roles import classify_role


def test_english_total_prefix_is_a_subtotal():
    assert classify_role("Total current assets", has_values=True, level=2) == "subtotal"


def test_japanese_gokei_suffix_is_a_subtotal():
    assert classify_role("流動資産合計", has_values=True, level=2) == "subtotal"
    assert classify_role("有形固定資産合計", has_values=True, level=3) == "subtotal"
