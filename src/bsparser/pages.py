"""Find the balance sheet page(s) of a PDF and cut one page out, so the page parser (page 1 only) is used unchanged."""
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pdfplumber

AMOUNT = re.compile(r"\d{1,3}(?:,\s?\d{3})+")
KEYWORDS = [  # (text, lowercase match, score)
    ("貸借対照表", False, 3), ("資産の部", False, 3), ("資産合計", False, 3),
    ("balance sheet", True, 3), ("total assets", True, 3), ("financial position", True, 2),
]


@dataclass
class Candidate:
    page: int  # 1-based
    score: float
    reason: str


def find_balance_sheet_pages(pdf_path) -> List[Candidate]:
    """Pages that look like a balance sheet, best first. Keyword hits plus how many thousands-grouped numbers it has."""
    found = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            hits = [word for word, lower, _ in KEYWORDS if (word in text.lower() if lower else word in text)]
            if not hits:
                continue
            score = sum(s for word, _, s in KEYWORDS if word in hits)
            amounts = len(AMOUNT.findall(text))
            score += min(amounts, 20) / 10
            found.append(Candidate(number, score, f"matches: {', '.join(hits)}; {amounts} grouped numbers"))
    return sorted(found, key=lambda c: (-c.score, c.page))


def extract_page(pdf_path, page: int, out_path) -> Path:
    """Write one page of a PDF to its own file, so the parser (which reads page 1) can be used unchanged."""
    subprocess.run(["pdfseparate", "-f", str(page), "-l", str(page), str(pdf_path), str(out_path)],
                   check=True, capture_output=True)
    return Path(out_path)
