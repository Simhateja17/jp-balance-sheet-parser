from dataclasses import dataclass, field
from typing import List

import pdfplumber

from bsparser.amounts import parse_amount
from bsparser.periods import find_periods

LINE_TOLERANCE = 2.0  # points: words whose tops differ by less sit on one line


@dataclass
class Line:
    label: str
    x0: float
    top: float
    amounts: List[str] = field(default_factory=list)


def _looks_like_garbled_amount(word: str) -> bool:
    """Mostly digits and commas with a stray letter, e.g. 1,2x4: an amount we cannot read, not label text."""
    digits = sum(ch.isdigit() for ch in word)
    strays = [ch for ch in word if not (ch.isdigit() or ch == ",")]
    return digits >= 2 and 0 < len(strays) <= 1 and strays[0].isalpha() and len(strays) / len(word) <= 0.25


def _is_amount(word: str) -> bool:
    return parse_amount(word).kind in ("value", "nil") or _looks_like_garbled_amount(word)


def extract_lines(pdf_path, page: int = 1) -> List[Line]:
    """Lines of one page (1-based), read straight from the file. No one-page copy is cut out first: cutting a page
    out of an encrypted PDF left a file pdfminer could not read."""
    with pdfplumber.open(pdf_path) as pdf:
        words = pdf.pages[page - 1].extract_words()
    return lines_from_words(words)


def _keep_date_tail_in_label(row: List[dict], split: int) -> int:
    """`As of March 31, 2025  As of March 31, 2026`: the last two tokens (31, and 2026) look like amounts but finish
    a date. Move just enough leading amount tokens back into the label to complete the date. A row such as
    `Balance at March 31, 2025  100  200` keeps its amounts, because they add no date."""
    label_text = " ".join(w["text"] for w in row[:split])
    dates = len(find_periods(label_text))
    for k in range(1, len(row) - split + 1):
        if len(find_periods(label_text + " " + " ".join(w["text"] for w in row[split:split + k]))) > dates:
            return split + k
    return split


def lines_from_words(words: List[dict]) -> List[Line]:
    rows: List[List[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(rows[-1][0]["top"] - word["top"]) <= LINE_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    lines = []
    for row in rows:
        row.sort(key=lambda w: w["x0"])
        split = len(row)
        while split > 0 and _is_amount(row[split - 1]["text"]):
            split -= 1
        split = _keep_date_tail_in_label(row, split)
        lines.append(Line(
            label=" ".join(w["text"] for w in row[:split]),
            x0=row[0]["x0"],
            top=row[0]["top"],
            amounts=[w["text"] for w in row[split:]],
        ))
    return lines
