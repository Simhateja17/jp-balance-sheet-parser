"""Run every PDF in data/heldout through the same path as the page and the command line: find the balance sheet
page, read the following pages of the statement, set the rounding mode from the cover hint, parse with the parser
unchanged, run the page checks and the cross-page checks. Nothing is picked by hand.

Run from the repo root: .venv/bin/python scripts/run_heldout.py <out_dir> [<in_dir>]   (in_dir defaults to data/heldout)
"""
import sys
import traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "src")
from bsparser.analyse import analyse_statement  # noqa: E402
from bsparser.output import write_statement_outputs  # noqa: E402

out_dir = Path(sys.argv[1])
in_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/heldout")
for pdf in sorted(in_dir.glob("*.pdf")):
    try:
        statement = analyse_statement(pdf)
    except Exception as exc:  # noqa: BLE001 - a crash is a result, shown and recorded, never hidden
        trace = traceback.format_exc().strip().splitlines()
        print("=" * 100)
        print(f"{pdf.name}: CRASH {type(exc).__name__}: {exc}")
        print("   ", trace[-3].strip())
        print("   ", trace[-2].strip()[:150])
        continue
    json_path, _ = write_statement_outputs(statement, out_dir)
    print("=" * 100)
    print(f"{pdf.name}: statement {statement['status']} | pages {[p['page'] for p in statement['pages']]} | "
          f"rounding {statement['rounding']} ({statement['rounding_source']})")
    if statement["rounding_sentence"] or statement["rounding_note"]:
        print("  ", statement["rounding_sentence"] or statement["rounding_note"])
    for page in statement["pages"]:
        counts = Counter(c["status"] for c in page["checks"])
        print(f"  page {page['page']}: {page['status']} unit={page['unit']} rows={len(page['rows'])} "
              f"checks={dict(counts)} issues={Counter(i['kind'] for i in page['issues'])}")
        for c in page["checks"]:
            if c["status"] != "pass":
                print("     check:", c["status"], c["label"], c["period"], "diff", c["difference"], "bound", c["bound"], c["reason"])
    cross = Counter(c["status"] for c in statement["cross_checks"])
    print(f"  cross-page checks: {dict(cross)}")
    for c in statement["cross_checks"]:
        print(f"     {c['status']:7s} {c['period']} {c['label']} printed={c['printed']} expected={c['expected']} diff={c['difference']} bound={c['bound']}")
