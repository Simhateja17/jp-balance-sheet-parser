import re
import unicodedata
from dataclasses import dataclass

import pdfplumber

COVER_PAGES = 3  # the cut-off sentence sits on the cover, not on the balance sheet page
CUT_OFF = re.compile(r"(百万円|千円|円)未満[^)\n]*?切(?:り)?捨て")
UNIT_OF = {"百万円": "million_yen", "千円": "thousand_yen", "円": "yen"}


@dataclass
class Hint:
    mode: str  # cut | unstated
    source: str  # cover_sentence | unstated
    sentence: str = ""
    note: str = ""


def find_rounding_hint(pdf_path, unit) -> Hint:
    """D18. A cut-off sentence on the first pages counts only when the unit it names is the balance sheet's unit.
    The parser never reads the cover otherwise and never guesses."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(unicodedata.normalize("NFKC", page.extract_text() or "") for page in pdf.pages[:COVER_PAGES])
    found = [(m.group(0), UNIT_OF[m.group(1)]) for m in CUT_OFF.finditer(text)]
    for sentence, sentence_unit in found:
        if sentence_unit == unit:
            return Hint("cut", "cover_sentence", sentence)
    if found:
        sentence, sentence_unit = found[0]
        return Hint("unstated", "unstated", sentence,
                    f"the cover says {sentence!r} (cut-off in {sentence_unit}) but the balance sheet is in {unit}: "
                    "rounding is not stated for this unit")
    return Hint("unstated", "unstated", "", "no cut-off sentence found on the first pages")
