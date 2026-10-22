from dataclasses import dataclass
from statistics import median
from typing import List

TIGHT_RATIO = 0.7  # a gap below this share of the median spacing looks like a wrapped line


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
    gaps = [b.top - a.top for a, b in zip(lines, lines[1:])]
    usual = median(gaps) if gaps else 0.0
    flagged = []
    for i, line in enumerate(lines[:-1]):
        nxt = lines[i + 1]
        if line.has_values:
            continue
        if nxt.has_values and nxt.level == line.level:
            flagged.append(WrappedFlag(i, "next line at the same level has values"))
        elif gaps[i] < TIGHT_RATIO * usual:
            flagged.append(WrappedFlag(i, "next line is much closer than the usual line spacing"))
    return flagged
