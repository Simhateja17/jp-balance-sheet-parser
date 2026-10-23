from bsparser.checks import bound_for


def test_round_and_unstated_use_the_strict_bound_and_cut_uses_the_item_count():
    assert [bound_for(n, "round") for n in (2, 3, 7, 10)] == [1, 2, 4, 5]
    assert [bound_for(n, "unstated") for n in (2, 3, 7, 10)] == [1, 2, 4, 5]  # same as round, assumed
    assert [bound_for(n, "cut") for n in (2, 3, 7, 10)] == [2, 3, 7, 10]  # |difference| <= items
