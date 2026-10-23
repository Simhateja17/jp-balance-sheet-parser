import json
import sys
from collections import Counter
from pathlib import Path

from bsparser.arbitrate import arbitrate
from bsparser.gold import evaluate, load_gold
from bsparser.output import build_output, output_from_page
from bsparser.page import parse_lines
from bsparser.report import _share
from bsparser.vision import lines_from_vision


def judge_replies(pdf_path, gold_path, reply_paths) -> str:
    """Judge saved vision replies with the same page rules, identity checks and gold as the text parser,
    and count the cells where vision and the text layer read different text."""
    golds = load_gold(gold_path)
    text = build_output(pdf_path)
    lines = ["| run | status | checks passed | gold exact | cells differing from the text layer |",
             "|---|---|---|---|---|"]
    for n, path in enumerate(reply_paths, start=1):
        reply = json.loads(Path(path).read_text(encoding="utf-8"))
        vision = output_from_page(parse_lines(lines_from_vision(reply)), f"vision run {n}")
        passed = sum(c["status"] == "pass" for c in vision["checks"])
        exact = sum(r.status == "exact" for r in evaluate(vision, golds))
        differing = len(arbitrate(text=text, vision=vision)["disagreements"])
        lines.append(f"| run {n} | {vision['status']} | {_share(passed, len(vision['checks'])).split(' (')[0]} "
                     f"| {_share(exact, len(golds))} | {differing} |")
    return "\n".join(lines) + "\n"


def main(argv) -> int:
    if len(argv) < 3:
        print("usage: python -m bsparser.vision_eval <pdf> <gold template> <reply.json> [more replies]", file=sys.stderr)
        return 2
    print(judge_replies(argv[0], argv[1], argv[2:]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
