from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Amount:
    value: Optional[int]


def parse_amount(raw: str) -> Amount:
    return Amount(value=int(raw.replace(",", "")))
