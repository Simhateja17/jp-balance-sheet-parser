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
