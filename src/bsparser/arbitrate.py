import copy
from typing import Dict

from bsparser.amounts import same_printed_text


def _score(output: Dict):
    """Lower is better: failed checks first, then skipped checks and unreadable values."""
    failed = sum(c["status"] == "failed" for c in output["checks"])
    doubtful = sum(c["status"] == "skipped" for c in output["checks"]) + sum(
        r["kind"] == "unreadable" for r in output["records"])
    return (failed, doubtful)


def _key(record: Dict):
    return (tuple(record["path"]), record["label"], record["period"])


def _flag_disagreements(winner: Dict, loser: Dict) -> None:
    """Every cell the two extractors read differently is flagged, even when both pass every check:
    two swapped rows in a section keep all sums intact, so agreement is extra evidence."""
    other = {_key(r): r for r in loser["records"]}
    winner["disagreements"] = []
    for rec in winner["records"]:
        theirs = other.get(_key(rec))
        if theirs is None or not same_printed_text(rec["raw"], theirs["raw"]):
            seen = "missing" if theirs is None else theirs["raw"]
            rec["warnings"].append(f"extractors_disagree: {winner['extractor']} {rec['raw']} vs {loser['extractor']} {seen}")
            winner["disagreements"].append({"key": list(_key(rec)), winner["extractor"]: rec["raw"], loser["extractor"]: seen})


def arbitrate(text: Dict, vision: Dict) -> Dict:
    """D7: better check result wins, a tie goes to text. No cell-level merging. Both outputs are kept."""
    text, vision = copy.deepcopy(text), copy.deepcopy(vision)
    text["extractor"], vision["extractor"] = "text", "vision"
    no_text = not text["records"] and bool(vision["records"])
    both_failed = _score(text)[0] > 0 and _score(vision)[0] > 0
    better_vision = _score(vision) < _score(text) and not both_failed
    winner, loser = (vision, text) if (no_text or better_vision) else (text, vision)
    _flag_disagreements(winner, loser)
    winner["alternative"] = loser
    winner["issues"].append({
        "kind": "extractor_chosen", "row_id": "",
        "message": ("no usable text layer: vision used; " if no_text else "")
                   + ("both failed their checks: text returned, vision attached for review; " if both_failed else "")
                   + f"{winner['extractor']} chosen: failed/doubtful checks {_score(winner)} against "
                   f"{loser['extractor']} {_score(loser)} (failed, skipped or unreadable)"})
    return winner
