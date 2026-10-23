"""Run chosen pages of the held-out PDFs as is (parser unchanged), catching crashes and showing them.

Run from the repo root:
  .venv/bin/python scripts/run_pages.py <out_dir> 140120260416505142.pdf:7 tanshin202603.pdf:6 ...
"""
import json
import sys
import tempfile
import traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")
from app import extract_page  # noqa: E402
from bsparser.output import build_output  # noqa: E402

out_dir = Path(sys.argv[1])
out_dir.mkdir(parents=True, exist_ok=True)
for spec in sys.argv[2:]:
    name, page = spec.rsplit(":", 1)
    print("=" * 100)
    print(name, "page", page)
    one_page = extract_page(Path("data/heldout") / name, int(page), Path(tempfile.mkdtemp()) / "page.pdf")
    try:
        out = build_output(one_page)
    except Exception as exc:  # shown, never hidden: a crash is a finding
        trace = traceback.format_exc().strip().splitlines()
        print("  CRASH:", type(exc).__name__, exc)
        print("   ", trace[-3].strip())
        print("   ", trace[-2].strip()[:140])
        continue
    counts = Counter(c["status"] for c in out["checks"])
    print(f"  status={out['status']} unit={out['unit']} periods={out['periods']} "
          f"rows={len(out['rows'])} records={len(out['records'])} checks={dict(counts)}")
    for issue in out["issues"]:
        print("   issue:", issue["kind"], issue["row_id"], issue["message"][:100])
    for check in out["checks"]:
        if check["status"] != "pass":
            print("   check:", check["status"], check["label"], check["period"], "diff", check["difference"], "bound", check["bound"])
    (out_dir / f"{Path(name).stem}_p{page}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
