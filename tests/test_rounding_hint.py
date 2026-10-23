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
