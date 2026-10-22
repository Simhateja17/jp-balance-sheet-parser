import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Gold:
    path: List[str]
    label: str
    role: str
    period: str
    raw: str  # as printed on the page, read by the user from the image


PERIOD_COLUMN = re.compile(r"raw (\d{4}-\d{2}-\d{2})")


def _cells(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_gold(template_path) -> List[Gold]:
    """Filled cells of the gold template. The key is (path, label, period), never the row number."""
    periods: List[str] = []
    gold: List[Gold] = []
    for line in Path(template_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("| #"):
            periods = PERIOD_COLUMN.findall(line)
        elif re.match(r"^\| \d+ \|", line):
            cells = _cells(line)
            path = [p for p in cells[1].split("/") if p]
            for period, raw in zip(periods, cells[6:6 + len(periods)]):
                if raw:
                    gold.append(Gold(path, cells[2], cells[4], period, raw))
    return gold
