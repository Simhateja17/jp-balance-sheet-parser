from pathlib import Path

from bsparser.pdf_lines import extract_lines

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def find(lines, label):
    matches = [line for line in lines if line.label == label]
    assert len(matches) == 1, (label, len(matches))
    return matches[0]


def test_line_has_label_left_x_and_raw_amounts():
    lines = extract_lines(FIXTURE_PDF)
    cash = find(lines, "Cash and deposits")
    assert cash.amounts == ["2,002,429", "608,281"]
    assert cash.x0 > 0


def word(text, x0, top):
    return {"text": text, "x0": x0, "top": top}


def test_token_that_is_mostly_digits_with_a_stray_letter_is_an_amount_not_label_text():
    from bsparser.pdf_lines import lines_from_words

    words = [word("Notes", 84.0, 100.0), word("receivable", 110.0, 100.0),
             word("1,2x4", 420.0, 100.0), word("200", 520.0, 100.0)]
    (line,) = lines_from_words(words)
    assert line.label == "Notes receivable"
    assert line.amounts == ["1,2x4", "200"]


def test_year_and_ordinary_words_are_not_mistaken_for_garbled_amounts():
    from bsparser.pdf_lines import lines_from_words

    words = [word("(Mar.", 300.0, 90.0), word("31,", 330.0, 90.0), word("2025)", 350.0, 90.0),
             word("Q3", 380.0, 90.0)]
    (line,) = lines_from_words(words)
    assert line.amounts == []
    assert line.label == "(Mar. 31, 2025) Q3"


def test_the_day_and_year_that_finish_a_date_stay_in_the_label_not_amounts():
    from bsparser.pdf_lines import lines_from_words

    words = [word(t, 300.0 + 30 * i, 120.0) for i, t in enumerate(
        ["As", "of", "March", "31,", "2025", "As", "of", "March", "31,", "2026"])]
    (line,) = lines_from_words(words)
    assert line.label == "As of March 31, 2025 As of March 31, 2026"
    assert line.amounts == []


def test_a_row_with_a_date_in_its_label_keeps_its_real_amounts():
    from bsparser.pdf_lines import lines_from_words

    words = [word(t, 60.0 + 40 * i, 200.0) for i, t in enumerate(["Balance", "at", "March", "31,", "2025"])]
    words += [word("100", 420.0, 200.0), word("200", 520.0, 200.0)]
    (line,) = lines_from_words(words)
    assert line.label == "Balance at March 31, 2025"
    assert line.amounts == ["100", "200"]


def test_a_page_can_be_read_straight_from_the_original_file_without_cutting_a_new_pdf():
    import tempfile

    from bsparser.pages import extract_page
    from bsparser.pdf_lines import extract_lines

    bank = Path(__file__).parent.parent / "data" / "heldout" / "tanshin202603.pdf"
    direct = extract_lines(bank, page=5)
    cut = extract_lines(extract_page(bank, 5, Path(tempfile.mkdtemp()) / "p.pdf"))
    assert [(l.label, l.amounts) for l in direct] == [(l.label, l.amounts) for l in cut]
    assert any(l.label == "資産の部合計" for l in direct)
