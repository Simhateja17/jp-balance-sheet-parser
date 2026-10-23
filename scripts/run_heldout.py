"""Run every PDF in data/heldout the way the Streamlit page does: find the best balance sheet page,
extract it, parse it with the parser unchanged, print status, checks and issues, save the JSON.

Run from the repo root: .venv/bin/python scripts/run_heldout.py <out_dir>
"""
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")
from app import extract_page, find_balance_sheet_pages  # noqa: E402
from bsparser.output import build_output  # noqa: E402

out_dir = Path(sys.argv[1])
out_dir.mkdir(parents=True, exist_ok=True)
for pdf in sorted(Path("data/heldout").glob("*.pdf")):
    candidates = find_balance_sheet_pages(pdf)
    print("=" * 100)
    print(pdf.name, "| candidates:", [(c.page, round(c.score, 1)) for c in candidates[:6]])
    if not candidates:
        print("  NO CANDIDATE PAGE")
        continue
    best = candidates[0]
    one_page = extract_page(pdf, best.page, Path(tempfile.mkdtemp()) / "page.pdf")
    out = build_output(one_page)
    counts = Counter(c["status"] for c in out["checks"])
    print(f"  page {best.page}: status={out['status']} unit={out['unit']} periods={out['periods']} "
          f"rows={len(out['rows'])} records={len(out['records'])} checks={dict(counts)}")
    for issue in out["issues"]:
        print("   issue:", issue["kind"], issue["row_id"], issue["message"][:110])
    for check in out["checks"]:
        if check["status"] != "pass":
            print("   check:", check["status"], check["label"], check["period"], "diff", check["difference"], "bound", check["bound"])
    (out_dir / f"{pdf.stem}_p{best.page}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
