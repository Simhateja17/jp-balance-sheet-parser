from bsparser.levels import assign_levels


def test_x_positions_within_tolerance_share_a_level():
    xs = [60.0, 60.4, 72.1, 71.8, 84.0, 59.7]
    assert assign_levels(xs, tolerance=2.0) == [0, 0, 1, 1, 2, 0]


def test_a_level_far_off_the_regular_step_is_irregular_and_a_regular_page_has_none():
    from bsparser.levels import irregular_levels

    regular = [60.0, 60.4, 72.1, 84.0, 83.7, 96.0, 108.2]
    assert irregular_levels(regular, tolerance=2.0) == []
    stray = [60.0, 72.0, 84.0, 90.0, 96.0, 108.0]  # 90 sits half a step off the 12-point grid
    assert irregular_levels(stray, tolerance=2.0) == [3]  # the level index of x = 90
    assert irregular_levels([60.0, 72.0], tolerance=2.0) == []  # too few levels to estimate a step
