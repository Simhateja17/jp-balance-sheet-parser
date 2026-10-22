from dataclasses import dataclass
from typing import Optional

NIL_MARKS = {"-", "\u2014", "\uff0d"}


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
