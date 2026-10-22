from collections import Counter
from typing import Dict, List

from bsparser.gold import Gold, Result


def _share(hits: int, total: int) -> str:
    """Always raw counts; a percentage only when there is something to divide by."""
    return f"{hits} of {total}" if total == 0 else f"{hits} of {total} ({round(100 * hits / total)}%)"


def _slices(output, golds: List[Gold]) -> Dict[str, List[int]]:
    label_counts = Counter(r["label"] for r in output["rows"])
    marks = ("-", "△0")
    pick = {
        "all": lambda g: True,
        "repeated labels": lambda g: label_counts[g.label] > 1,
        "nil and zero-with-mark": lambda g: g.raw.replace("－", "-").replace(" ", "") in marks,
        "net and contra": lambda g: g.role in ("net", "contra"),
    }
    return {name: [i for i, g in enumerate(golds) if keep(g)] for name, keep in pick.items()}


def summarise(output, golds: List[Gold], parser: List[Result], baseline: List[Result]) -> Dict[str, Dict[str, str]]:
    table = {}
    for name, idx in _slices(output, golds).items():
        wrong = [parser[i] for i in idx if parser[i].status != "exact"]
        table[name] = {
            "parser_exact": _share(sum(parser[i].status == "exact" for i in idx), len(idx)),
            "parser_value_exact": _share(sum(parser[i].value_ok for i in idx), len(idx)),
            "baseline_exact": _share(sum(baseline[i].status == "exact" for i in idx), len(idx)),
            "parser_silent_errors": _share(sum(not r.flagged for r in wrong), len(idx)),
            "parser_flagged_errors": _share(sum(r.flagged for r in wrong), len(idx)),
        }
    return table
