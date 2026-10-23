import tempfile
from pathlib import Path
from typing import Dict, Optional

import pdfplumber

from bsparser.output import output_from_page
from bsparser.page import parse_page
from bsparser.pages import extract_page, find_balance_sheet_pages
from bsparser.rounding import find_rounding_hint

ROUNDING_CHOICES = ("auto", "round", "cut", "unstated")


def analyse(pdf_path, page: Optional[int] = None, rounding: str = "auto") -> Dict:
    """One path for the command line, the held-out script and the page, so no result depends on hand-picked options.
    Finds the balance sheet page (unless given), parses it with the parser unchanged, and sets the rounding mode:
    `auto` takes the cover hint (D18), an explicit value is recorded as chosen by the user."""
    with pdfplumber.open(pdf_path) as pdf:
        pages_total = len(pdf.pages)
    if page is None:
        candidates = find_balance_sheet_pages(pdf_path)
        page = candidates[0].page if candidates else 1
    one_page = extract_page(pdf_path, page, Path(tempfile.mkdtemp(prefix="bsparser_")) / "page.pdf")
    parsed = parse_page(one_page)
    if rounding == "auto":
        hint = find_rounding_hint(pdf_path, parsed.unit)
        mode, source, sentence, note = hint.mode, hint.source, hint.sentence, hint.note
    else:
        mode, source, sentence, note = rounding, "user", "", ""
    out = output_from_page(parsed, str(pdf_path), rounding=mode, rounding_source=source,
                           rounding_sentence=sentence, rounding_note=note)
    out["page"], out["pages_total"] = page, pages_total
    return out
