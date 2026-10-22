from bsparser.periods import find_periods


def test_japanese_gregorian_dates_with_fullwidth_digits_and_optional_spaces():
    assert find_periods("(2025年３月31日) (2026年３月31日)") == ["2025-03-31", "2026-03-31"]
    assert find_periods("(2025 年３月 31 日) (2026 年３月 31 日)") == ["2025-03-31", "2026-03-31"]


def test_english_dates_still_work():
    assert find_periods("(Mar. 31, 2025) (Mar. 31, 2026)") == ["2025-03-31", "2026-03-31"]
