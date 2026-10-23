"""Find the balance sheet page(s) of a PDF and cut one page out, so the page parser (page 1 only) is used unchanged."""
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pdfplumber

AMOUNT = re.compile(r"\d{1,3}(?:,\s?\d{3})+")
KEYWORDS = [  # (text, lowercase match, score)
    ("貸借対照表", False, 3), ("資産の部", False, 3), ("資産合計", False, 3),
    ("balance sheet", True, 3), ("total assets", True, 3), ("financial position", True, 2),
]


TITLE = re.compile(r"貸借対照表|balance sheet|financial position", re.I)
ASSETS_PART = re.compile(r"資産の部|total assets|^\s*assets\s*$", re.I | re.M)
TOTAL_ASSETS_LINE = re.compile(r"^\s*(?:資産合計|資産の部合計|total assets)", re.I | re.M)
HEADING_WORDS = re.compile(r"財務諸表|financial statements|貸借対照表|balance sheet|financial position", re.I)


@dataclass
class Candidate:
    page: int  # 1-based
    score: float
    reason: str
    heading: str = ""  # e.g. "4. 個別財務諸表 / (1) 貸借対照表", so consolidated and parent-only statements read apart


def _heading(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()[:8] if HEADING_WORDS.search(line)]
    return " / ".join(lines[:2])


def find_balance_sheet_pages(pdf_path, strict: bool = True) -> List[Candidate]:
    """Pages that look like a balance sheet, best first.
    strict (the default): the page has a balance-sheet title, an assets part and a total-assets line, all three.
    Liabilities pages are not offered: they are read together with their assets page (statement mode).
    strict=False: any page with a keyword, for the 'my page is not listed' escape."""
    found = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            raw = page.extract_text() or ""
            text = unicodedata.normalize("NFKC", raw)
            if strict and not (TITLE.search(text) and ASSETS_PART.search(text) and TOTAL_ASSETS_LINE.search(text)):
                continue
            hits = [word for word, lower, _ in KEYWORDS if (word in text.lower() if lower else word in text)]
            if not hits:
                continue
            score = sum(s for word, _, s in KEYWORDS if word in hits)
            amounts = len(AMOUNT.findall(text))
            score += min(amounts, 20) / 10
            found.append(Candidate(number, score, f"matches: {', '.join(hits)}; {amounts} grouped numbers", _heading(raw)))
    return sorted(found, key=lambda c: (-c.score, c.page))


def extract_page(pdf_path, page: int, out_path) -> Path:
    """Write one page of a PDF to its own file, so the parser (which reads page 1) can be used unchanged."""
    subprocess.run(["pdfseparate", "-f", str(page), "-l", str(page), str(pdf_path), str(out_path)],
                   check=True, capture_output=True)
    return Path(out_path)
