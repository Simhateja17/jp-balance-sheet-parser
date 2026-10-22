from dataclasses import asdict
from typing import Dict

from bsparser.checks import run_checks
from bsparser.page import parse_page
from bsparser.records import make_records
from bsparser.status import page_status


def build_output(pdf_path) -> Dict:
    page = parse_page(pdf_path)
    checks = run_checks(page)
    return {
        "source": str(pdf_path),
        "status": page_status(page, checks),
        "unit": page.unit,
        "unit_raw": page.unit_raw,
        "periods": page.periods,
        "issues": [asdict(i) for i in page.issues],
        "checks": [asdict(c) for c in checks],
        "rows": [
            {"id": r.id, "label": r.label, "label_en": r.label, "label_en_source": "original",
             "role": r.role, "level": r.level, "parent": r.parent, "path": list(r.path)}
            for r in page.rows
        ],
        "records": make_records(page),
    }
