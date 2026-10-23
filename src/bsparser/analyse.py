import re
import tempfile
from pathlib import Path
from typing import Dict, Optional

import pdfplumber

from bsparser.output import output_from_page
from bsparser.page import parse_page
from bsparser.pages import extract_page, find_balance_sheet_pages
from bsparser.rounding import find_rounding_hint
from bsparser.statement import cross_checks

ROUNDING_CHOICES = ("auto", "round", "cut", "unstated")


def _page_output(pdf_path, page: int, pages_total: int, mode: str, source: str, sentence: str, note: str,
                 parsed=None) -> Dict:
    if parsed is None:
        parsed = parse_page(pdf_path, page)
    out = output_from_page(parsed, str(pdf_path), rounding=mode, rounding_source=source,
                           rounding_sentence=sentence, rounding_note=note)
    out["page"], out["pages_total"] = page, pages_total
    return out


def _parse(pdf_path, page: int):
    return parse_page(pdf_path, page)  # straight from the original file, no page cut out (encrypted PDFs)


def _resolve_rounding(pdf_path, unit, rounding: str):
    if rounding == "auto":
        hint = find_rounding_hint(pdf_path, unit)
        return hint.mode, hint.source, hint.sentence, hint.note
    return rounding, "user", "", ""


def analyse(pdf_path, page: Optional[int] = None, rounding: str = "auto") -> Dict:
    """One path for the command line, the held-out script and the page, so no result depends on hand-picked options.
    Finds the balance sheet page (unless given), parses it with the parser unchanged, and sets the rounding mode:
    `auto` takes the cover hint (D18), an explicit value is recorded as chosen by the user."""
    with pdfplumber.open(pdf_path) as pdf:
        pages_total = len(pdf.pages)
    if page is None:
        candidates = find_balance_sheet_pages(pdf_path) or find_balance_sheet_pages(pdf_path, strict=False)
        page = candidates[0].page if candidates else 1
    parsed = _parse(pdf_path, page)
    mode, source, sentence, note = _resolve_rounding(pdf_path, parsed.unit, rounding)
    return _page_output(pdf_path, page, pages_total, mode, source, sentence, note, parsed=parsed)


CONTINUES = re.compile(r"負債の部|純資産の部|負債合計|純資産合計|負債純資産合計|total liabilities|total net assets|total equity", re.I)
MAX_FOLLOWING = 2
RANK = {"ok": 0, "failed": 1, "unreadable": 2}


def analyse_statement(pdf_path, page: Optional[int] = None, rounding: str = "auto") -> Dict:
    """Q23. The assets page plus the following pages (up to 2) with the same unit and periods that carry liabilities
    or net assets wording, each parsed page by page with the parser unchanged, then checked across pages.
    The rounding mode is resolved once, from the assets page, so every page uses the same one."""
    with pdfplumber.open(pdf_path) as pdf:
        pages_total = len(pdf.pages)
        texts = {n: pdf.pages[n - 1].extract_text() or "" for n in range(1, pages_total + 1)}
    if page is None:
        candidates = find_balance_sheet_pages(pdf_path) or find_balance_sheet_pages(pdf_path, strict=False)
        page = candidates[0].page if candidates else 1
    first = _parse(pdf_path, page)
    mode, source, sentence, note = _resolve_rounding(pdf_path, first.unit, rounding)
    outputs = [_page_output(pdf_path, page, pages_total, mode, source, sentence, note, parsed=first)]
    for nxt in range(page + 1, min(page + MAX_FOLLOWING, pages_total) + 1):
        if not CONTINUES.search(texts[nxt]):
            break
        parsed = _parse(pdf_path, nxt)
        if (parsed.unit, parsed.periods) != (first.unit, first.periods):
            break
        outputs.append(_page_output(pdf_path, nxt, pages_total, mode, source, sentence, note, parsed=parsed))
    cross = cross_checks(outputs, mode)
    worst = max([o["status"] for o in outputs] + (["failed"] if any(c["status"] == "failed" for c in cross) else []),
                key=RANK.get)
    return {"source": str(pdf_path), "status": worst, "rounding": mode, "rounding_source": source,
            "rounding_sentence": sentence, "rounding_note": note, "pages": outputs, "cross_checks": cross}
