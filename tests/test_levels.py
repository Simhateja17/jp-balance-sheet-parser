from bsparser.levels import assign_levels


def test_x_positions_within_tolerance_share_a_level():
    xs = [60.0, 60.4, 72.1, 71.8, 84.0, 59.7]
    assert assign_levels(xs, tolerance=2.0) == [0, 0, 1, 1, 2, 0]
