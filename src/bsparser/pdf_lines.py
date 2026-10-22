from dataclasses import dataclass, field
from typing import List

import pdfplumber

from bsparser.amounts import parse_amount

LINE_TOLERANCE = 2.0  # points: words whose tops differ by less sit on one line


@dataclass
class Line:
    label: str
    x0: float
    top: float
    amounts: List[str] = field(default_factory=list)


def _is_amount(word: str) -> bool:
    return parse_amount(word).kind in ("value", "nil")


def extract_lines(pdf_path) -> List[Line]:
    with pdfplumber.open(pdf_path) as pdf:
        words = pdf.pages[0].extract_words()
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
        lines.append(Line(
            label=" ".join(w["text"] for w in row[:split]),
            x0=row[0]["x0"],
            top=row[0]["top"],
            amounts=[w["text"] for w in row[split:]],
        ))
    return lines
