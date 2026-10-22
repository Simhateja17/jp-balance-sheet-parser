from bsparser.roles import classify_role


def test_english_total_prefix_is_a_subtotal():
    assert classify_role("Total current assets", has_values=True, level=2) == "subtotal"
