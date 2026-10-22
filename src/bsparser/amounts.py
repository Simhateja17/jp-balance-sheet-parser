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
    return Amount(value=int(text.replace(",", "")), kind="value")
