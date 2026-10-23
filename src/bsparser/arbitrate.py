import copy
from typing import Dict


def _score(output: Dict):
    """Lower is better: failed checks first, then skipped checks and unreadable values."""
    failed = sum(c["status"] == "failed" for c in output["checks"])
    doubtful = sum(c["status"] == "skipped" for c in output["checks"]) + sum(
        r["kind"] == "unreadable" for r in output["records"])
    return (failed, doubtful)


def arbitrate(text: Dict, vision: Dict) -> Dict:
    """D7: better check result wins, a tie goes to text. No cell-level merging. Both outputs are kept."""
    text, vision = copy.deepcopy(text), copy.deepcopy(vision)
    text["extractor"], vision["extractor"] = "text", "vision"
    winner, loser = (vision, text) if _score(vision) < _score(text) else (text, vision)
    winner["alternative"] = loser
    winner["issues"].append({
        "kind": "extractor_chosen", "row_id": "",
        "message": f"{winner['extractor']} chosen: failed/doubtful checks {_score(winner)} against "
                   f"{loser['extractor']} {_score(loser)} (failed, skipped or unreadable)"})
    return winner
