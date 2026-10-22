import sys
from pathlib import Path

from bsparser.baseline import first_match
from bsparser.checks import run_checks
from bsparser.gold import evaluate, gold_page, load_gold
from bsparser.output import build_output
from bsparser.report import render_markdown, summarise

LIMITS = [
    "Gold values were read from the page image by a separate Claude session, not by a human, and not from the text "
    "layer or the parser. A reading error shared by two models is possible.",
    "The parser rules were developed on this same page, so a perfect score here is in-sample. It is not evidence "
    "about other filings. Held-out layouts (messy English variant, other filings) are still to be measured.",
    "The baseline is a deliberately naive lookup: first line with the same label, section path ignored.",
    "Gold is compared as printed text. The parser's own sign and nil rules are covered by separate unit tests.",
]


def accuracy_markdown(pdf_path, template_path, title: str) -> str:
    golds = load_gold(template_path)
    out = build_output(pdf_path)
    parser = evaluate(out, golds)
    baseline = first_match(pdf_path, golds)
    gold_checks = run_checks(gold_page(template_path))
    gold_pass = sum(c.status == "pass" for c in gold_checks)
    wrong = [r for r in baseline if r.status != "exact"]
    lines = [render_markdown(f"{title}: {len(golds)} gold cells, page status {out['status']}",
                             summarise(out, golds, parser, baseline))]
    lines.append(f"Gold values pass the accounting identities: {gold_pass} of {len(gold_checks)}")
    lines.append("")
    lines.append(f"first-match baseline errors: {len(wrong)} of {len(golds)}")
    for r in wrong:
        lines.append(f"- {'/'.join(r.gold.path)} / {r.gold.label} / {r.gold.period} / gold {r.gold.raw}")
    lines.append("")
    lines.append("Limits:")
    lines.extend(f"- {text}" for text in LIMITS)
    return "\n".join(lines) + "\n"


def main(argv) -> int:
    if len(argv) != 4:
        print("usage: python -m bsparser.accuracy <pdf> <gold template> <title> <out file>", file=sys.stderr)
        return 2
    Path(argv[3]).write_text(accuracy_markdown(argv[0], argv[1], argv[2]), encoding="utf-8")
    print(f"wrote {argv[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
