from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Amount:
    value: Optional[int]
    kind: str


def parse_amount(raw: str) -> Amount:
    text = raw.strip()
    if text == "-":
        return Amount(value=None, kind="nil")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    value = int(text.replace(",", ""))
    return Amount(value=-value if negative else value, kind="value")
