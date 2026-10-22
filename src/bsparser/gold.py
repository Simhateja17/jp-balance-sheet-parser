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


@dataclass
class Result:
    gold: Gold
    status: str  # exact | wrong_value | wrong_role | not_found | ambiguous
    flagged: bool  # the parser warned about this record, its row, or the whole page
    value_ok: bool = False  # layer 1: the printed text matches exactly
    role_ok: bool = False  # layer 2: the role matches (the path is part of the key)


def evaluate(output, golds: List[Gold]) -> List[Result]:
    results = []
    for g in golds:
        matches = [r for r in output["records"]
                   if r["path"] == g.path and r["label"] == g.label and r["period"] == g.period]
        if len(matches) != 1:
            results.append(Result(g, "not_found" if not matches else "ambiguous", True))
            continue
        rec = matches[0]
        flagged = bool(rec["warnings"]) or output["status"] != "ok"
        value_ok = rec["raw"] == g.raw
        role_ok = rec["role"] == g.role
        status = "wrong_value" if not value_ok else ("exact" if role_ok else "wrong_role")
        results.append(Result(g, status, flagged, value_ok, role_ok))
    return results
