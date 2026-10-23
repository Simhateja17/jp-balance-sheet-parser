import re
import unicodedata
from dataclasses import dataclass

import pdfplumber

COVER_PAGES = 3  # the cut-off sentence sits on the cover, not on the balance sheet page
CUT_OFF = re.compile(r"(百万円|千円|円)未満[^)\n]*?切(?:り)?捨て")
UNIT_OF = {"百万円": "million_yen", "千円": "thousand_yen", "円": "yen"}
ENGLISH_UNIT_OF = {"million": "million_yen", "thousand": "thousand_yen"}
CUT_VERB = r"(?:disregarded|truncated|discarded|omitted|ignored|cut off|rounded down)"
# "any amount less than one million yen is disregarded" / "amounts below one thousand yen are truncated"
ENGLISH_LESS_THAN = re.compile(r"(?:less than|below|under) (?:one )?(million|thousand) yen[^.]{0,40}?" + CUT_VERB)
# "yen amounts are rounded down to millions" / "truncated to the nearest thousand yen"
ENGLISH_DOWN_TO = re.compile(r"(?:rounded down|truncated|cut off) to (?:the nearest )?(?:one )?(million|thousand)s?(?: of)?(?: yen)?")


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
    english = " ".join(text.lower().split())  # one line, so a sentence broken across lines still matches
    for pattern in (ENGLISH_LESS_THAN, ENGLISH_DOWN_TO):
        found += [(m.group(0), ENGLISH_UNIT_OF[m.group(1)]) for m in pattern.finditer(english)]
    for sentence, sentence_unit in found:
        if sentence_unit == unit:
            return Hint("cut", "cover_sentence", sentence)
    if found:
        sentence, sentence_unit = found[0]
        return Hint("unstated", "unstated", sentence,
                    f"the cover says {sentence!r} (cut-off in {sentence_unit}) but the balance sheet is in {unit}: "
                    "rounding is not stated for this unit")
    return Hint("unstated", "unstated", "", "no cut-off sentence found on the first pages")
