from dataclasses import dataclass
from typing import Optional

NIL_MARKS = {"-", "\u2014", "\uff0d"}


@dataclass(frozen=True)
class Amount:
    value: Optional[int]
    kind: str


def parse_amount(raw: str) -> Amount:
    text = raw.strip()
    if text in NIL_MARKS:
        return Amount(value=None, kind="nil")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    elif text.startswith("\u25b3"):
        negative = True
        text = text[1:]
    value = int(text.replace(",", ""))
    return Amount(value=-value if negative else value, kind="value")
