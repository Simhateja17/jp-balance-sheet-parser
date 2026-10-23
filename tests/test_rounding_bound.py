from bsparser.checks import bound_for


def test_round_and_unstated_use_the_strict_bound_and_cut_uses_the_item_count():
    assert [bound_for(n, "round") for n in (2, 3, 7, 10)] == [1, 2, 4, 5]
    assert [bound_for(n, "unstated") for n in (2, 3, 7, 10)] == [1, 2, 4, 5]  # same as round, assumed
    assert [bound_for(n, "cut") for n in (2, 3, 7, 10)] == [2, 3, 7, 10]  # |difference| <= items


def seven_item_page(printed_prior):
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    items = [Line(f"item {n}", 84.0, 148.0 + 14 * n, ["100", "100"]) for n in range(7)]
    return parse_lines([
        Line("（単位：百万円）", 400.0, 70.0),
        Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
        Line("資産の部", 60.0, 120.0),
        Line("流動資産", 72.0, 134.0),
        *items,
        Line("流動資産合計", 84.0, 148.0 + 14 * 7, [printed_prior, "704"]),
    ])


def test_the_same_difference_fails_under_unstated_and_passes_under_cut():
    from bsparser.checks import run_checks

    page = seven_item_page("705")  # items sum to 700: difference 5 in 2025 and 4 in 2026
    unstated = run_checks(page)  # default is unstated
    assert [(c.difference, c.bound, c.status) for c in unstated] == [(5, 4, "failed"), (4, 4, "pass")]
    cut = run_checks(page, rounding="cut")
    assert [(c.difference, c.bound, c.status) for c in cut] == [(5, 7, "pass"), (4, 7, "pass")]
    over = run_checks(seven_item_page("708"), rounding="cut")  # difference 8 is still beyond the cut bound
    assert [(c.difference, c.bound, c.status) for c in over][0] == (8, 7, "failed")
