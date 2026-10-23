import unicodedata
from dataclasses import dataclass
from typing import Optional

# hyphen, en dash, em dash, horizontal bar (the long bar), minus sign, full-width hyphen: alone, each is a printed nil
NIL_MARKS = {"-", "\u2013", "\u2014", "\u2015", "\u2212", "\uff0d"}


@dataclass(frozen=True)
class Amount:
    value: Optional[int]
    kind: str
    raw: str = ""


def parse_amount(raw: str) -> Amount:
    text = raw.strip()
    if text in NIL_MARKS:
        return Amount(value=None, kind="nil", raw=raw)
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    elif text.startswith(("\u25b3", "-")):
        negative = True
        text = text[1:]
    digits = text.replace(",", "")
    if not digits.isdigit():
        return Amount(value=None, kind="unreadable", raw=raw)
    value = int(digits)
    return Amount(value=-value if negative else value, kind="value", raw=raw)


def same_printed_text(printed: str, other: str) -> bool:
    """Width and spacing are typing noise (full-width digits, spaces). Every nil mark is the same nil.
    Other marks are not noise: a triangle zero is not (0), and nil is never 0."""
    def norm(text: str) -> str:
        text = unicodedata.normalize("NFKC", text).replace(" ", "")
        return "-" if text in NIL_MARKS else text
    return norm(printed) == norm(other)
