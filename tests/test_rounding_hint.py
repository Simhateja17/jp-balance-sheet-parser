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


FRESH = Path(__file__).parent.parent / "data" / "fresh"


def test_english_cover_cut_off_sentences_are_read_when_the_unit_matches():
    yokogawa = find_rounding_hint(FRESH / "ir_202603tanshin-en.pdf", "million_yen")
    assert (yokogawa.mode, yokogawa.source) == ("cut", "cover_sentence")
    assert "disregarded" in yokogawa.sentence
    shimadzu = find_rounding_hint(FRESH / "vg1mvt19a00h4bsv.pdf", "million_yen")
    assert (shimadzu.mode, shimadzu.source) == ("cut", "cover_sentence")
    assert "rounded down" in shimadzu.sentence
    mismatch = find_rounding_hint(FRESH / "ir_202603tanshin-en.pdf", "thousand_yen")
    assert (mismatch.mode, mismatch.source) == ("unstated", "unstated") and "thousand_yen" in mismatch.note


import pytest


@pytest.mark.parametrize("sentence,unit,mode", [
    ("Amounts less than one million yen are truncated.", "million_yen", "cut"),
    ("Figures are rounded down to the nearest million yen.", "million_yen", "cut"),
    ("Amounts of less than one thousand yen are discarded.", "thousand_yen", "cut"),
    ("(Any amount less than one\nmillion yen is disregarded.)", "million_yen", "cut"),  # broken across a line
    ("Ratios are rounded down to one decimal place.", "million_yen", "unstated"),  # not an amount cut-off
    ("Amounts are rounded to the nearest million yen.", "million_yen", "unstated"),  # rounding, not a cut-off: not read as cut
])
def test_english_cut_off_wording_variants_and_things_that_must_not_count(tmp_path, sentence, unit, mode):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path = tmp_path / "cover.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 780
    for line in sentence.split("\n"):
        c.drawString(60, y, line)
        y -= 14
    c.save()
    assert find_rounding_hint(path, unit).mode == mode
