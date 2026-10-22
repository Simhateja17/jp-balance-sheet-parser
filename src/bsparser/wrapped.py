from dataclasses import dataclass
from typing import List


@dataclass
class LineInfo:
    label: str
    has_values: bool
    level: int
    top: float


@dataclass
class WrappedFlag:
    index: int
    reason: str


def find_possible_wrapped(lines: List[LineInfo]) -> List[WrappedFlag]:
    flagged = []
    for i, line in enumerate(lines[:-1]):
        nxt = lines[i + 1]
        if not line.has_values and nxt.has_values and nxt.level == line.level:
            flagged.append(WrappedFlag(i, "next line at the same level has values"))
    return flagged
