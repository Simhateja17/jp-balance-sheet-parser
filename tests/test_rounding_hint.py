from pathlib import Path

from bsparser.rounding import find_rounding_hint

HELDOUT = Path(__file__).parent.parent / "data" / "heldout"


def test_a_cover_cut_off_sentence_in_the_balance_sheet_unit_gives_cut_with_its_source_and_sentence():
    hint = find_rounding_hint(HELDOUT / "140120260416505142.pdf", "million_yen")
    assert (hint.mode, hint.source) == ("cut", "cover_sentence")
    assert "百万円未満切捨て" in hint.sentence
    bank = find_rounding_hint(HELDOUT / "tanshin202603.pdf", "million_yen")
    assert (bank.mode, bank.source) == ("cut", "cover_sentence")
    assert "百万円未満" in bank.sentence and "切捨て" in bank.sentence


def test_a_cut_off_stated_for_another_unit_is_unstated_with_the_reason():
    hint = find_rounding_hint(HELDOUT / "140120260514535920.pdf", "thousand_yen")  # 2452: cover says millions
    assert (hint.mode, hint.source) == ("unstated", "unstated")
    assert "million_yen" in hint.note and "thousand_yen" in hint.note
    assert "百万円未満切捨て" in hint.sentence


def test_no_cut_off_sentence_means_unstated():
    root = Path(__file__).parent.parent / "data"
    hint = find_rounding_hint(root / "balance_sheet_after_correction.pdf", "thousand_yen")
    assert (hint.mode, hint.source, hint.sentence) == ("unstated", "unstated", "")
    assert "no cut-off sentence" in hint.note
    assert find_rounding_hint(HELDOUT / "140120260513529466.pdf", "million_yen").mode == "cut"  # 4224
