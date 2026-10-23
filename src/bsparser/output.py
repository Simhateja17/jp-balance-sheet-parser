import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from bsparser.checks import run_checks
from bsparser.labels import english_label
from bsparser.page import parse_page
from bsparser.records import make_records
from bsparser.status import page_status


def build_output(pdf_path, **rounding) -> Dict:
    return output_from_page(parse_page(pdf_path), str(pdf_path), **rounding)


def output_from_page(page, source: str, rounding: str = "unstated", rounding_source: str = "unstated",
                     rounding_sentence: str = "", rounding_note: str = "") -> Dict:
    checks = run_checks(page, rounding)
    if rounding == "unstated" and not rounding_note:
        rounding_note = "rounding: unstated, strict bound used"
    return {
        "source": source,
        "status": page_status(page, checks),
        "rounding": rounding,
        "rounding_source": rounding_source,
        "rounding_sentence": rounding_sentence,
        "rounding_note": rounding_note,
        "unit": page.unit,
        "unit_raw": page.unit_raw,
        "periods": page.periods,
        "issues": [asdict(i) for i in page.issues],
        "checks": [asdict(c) for c in checks],
        "rows": [
            {"id": r.id, "label": r.label, "label_en": english_label(r.label)[0],
             "label_en_source": english_label(r.label)[1],
             "role": r.role, "level": r.level, "parent": r.parent, "path": list(r.path)}
            for r in page.rows
        ],
        "records": make_records(page),
    }


RECORD_COLUMNS = ["id", "path", "label", "label_en", "label_en_source", "role", "parent",
                  "period", "value", "kind", "raw", "unit", "warnings"]


def write_outputs(pdf_path, out_dir, output=None):
    """JSON is the source of truth (D1); the records CSV is a view of it."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = output if output is not None else build_output(pdf_path)
    stem = Path(pdf_path).stem
    json_path = out_dir / f"{stem}.json"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    csv_path = out_dir / f"{stem}.records.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RECORD_COLUMNS)
        writer.writeheader()
        for rec in out["records"]:
            row = dict(rec)
            row["path"] = " / ".join(rec["path"])
            row["value"] = "" if rec["value"] is None else rec["value"]
            row["parent"] = rec["parent"] or ""
            row["warnings"] = "; ".join(rec["warnings"])
            writer.writerow(row)
    return json_path, csv_path
