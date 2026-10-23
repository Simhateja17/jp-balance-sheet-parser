"""Try the balance sheet parser: drop in a PDF, see the table, status, checks and issues, download the CSV.

Run: .venv/bin/streamlit run app.py   (the parser in src/bsparser is used as is)
"""
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pdfplumber  # noqa: E402

from bsparser.output import build_output, write_outputs  # noqa: E402

AMOUNT = re.compile(r"\d{1,3}(?:,\s?\d{3})+")
KEYWORDS = [  # (text, lowercase match, score)
    ("貸借対照表", False, 3), ("資産の部", False, 3), ("資産合計", False, 3),
    ("balance sheet", True, 3), ("total assets", True, 3), ("financial position", True, 2),
]


@dataclass
class Candidate:
    page: int  # 1-based
    score: float
    reason: str


def find_balance_sheet_pages(pdf_path) -> List[Candidate]:
    """Pages that look like a balance sheet, best first. Keyword hits plus how many thousands-grouped numbers it has."""
    found = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            hits = [word for word, lower, _ in KEYWORDS if (word in text.lower() if lower else word in text)]
            if not hits:
                continue
            score = sum(s for word, _, s in KEYWORDS if word in hits)
            amounts = len(AMOUNT.findall(text))
            score += min(amounts, 20) / 10
            found.append(Candidate(number, score, f"matches: {', '.join(hits)}; {amounts} grouped numbers"))
    return sorted(found, key=lambda c: (-c.score, c.page))


def extract_page(pdf_path, page: int, out_path) -> Path:
    """Write one page of a PDF to its own file, so the parser (which reads page 1) can be used unchanged."""
    subprocess.run(["pdfseparate", "-f", str(page), "-l", str(page), str(pdf_path), str(out_path)],
                   check=True, capture_output=True)
    return Path(out_path)


def table_rows(output: dict) -> List[dict]:
    """One display row per table row: indented label, English reading label, role, and the printed value per period."""
    raw = {(r["id"].split("|")[0], r["period"]): r["raw"] for r in output["records"]}
    rows = []
    for row in output["rows"]:
        line = {"label": "   " * row["level"] + row["label"], "label_en": row["label_en"] or "", "role": row["role"]}
        for period in output["periods"]:
            line[period] = raw.get((row["id"], period), "")
        rows.append(line)
    return rows


STATUS_TEXT = {
    "ok": "ok: every identity check holds within the rounding bound",
    "failed": "failed: at least one identity check is beyond its bound",
    "unreadable": "unreadable: a value, unit, period or column could not be read; see the issues",
}


def main() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="Balance sheet parser", layout="wide")
    st.title("Balance sheet parser")
    st.caption("Drop in a PDF. The page that looks like a balance sheet is found, parsed by the text layer "
               "(no OCR, no vision model here), and checked with accounting identities.")
    upload = st.file_uploader("PDF", type="pdf")
    if upload is None:
        return
    work = Path(tempfile.mkdtemp(prefix="bsparser_"))
    source = work / "upload.pdf"
    source.write_bytes(upload.getvalue())
    with pdfplumber.open(source) as pdf:
        total_pages = len(pdf.pages)

    candidates = find_balance_sheet_pages(source)
    if candidates:
        labels = [f"page {c.page}: {c.reason}" for c in candidates]
        choice = st.selectbox(f"{total_pages} pages. Balance sheet candidates, best first", labels)
        page = candidates[labels.index(choice)].page
    else:
        st.warning("No page looks like a balance sheet (no keywords such as 貸借対照表 or Total assets). Pick a page to try anyway.")
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    page = int(page)

    one_page = extract_page(source, page, work / f"{Path(upload.name).stem}_p{page}.pdf")
    output = build_output(one_page)
    json_path, csv_path = write_outputs(one_page, work / "out")

    st.subheader(f"Status: {output['status']}")
    {"ok": st.success, "failed": st.error, "unreadable": st.warning}[output["status"]](STATUS_TEXT[output["status"]])
    left, mid, right = st.columns(3)
    left.metric("Unit", f"{output['unit'] or 'not found'}", output["unit_raw"] or None)
    mid.metric("Periods", ", ".join(output["periods"]) or "not found")
    right.metric("Rows / records", f"{len(output['rows'])} / {len(output['records'])}")

    if not output["rows"]:
        st.error("No table rows were found on this page. The parser needs a text layer; a scanned page has none.")
    else:
        st.subheader("Table")
        st.dataframe(pd.DataFrame(table_rows(output)), hide_index=True, width="stretch")

    st.subheader(f"Checks ({len(output['checks'])})")
    if output["checks"]:
        shown = pd.DataFrame(output["checks"]).drop(columns=["row_id"])
        shown.insert(0, "result", shown.pop("status").map({"pass": "pass", "failed": "FAILED", "skipped": "skipped"}))
        st.dataframe(shown, hide_index=True, width="stretch")
    else:
        st.info("No identity checks could be run on this page.")

    st.subheader(f"Issues ({len(output['issues'])})")
    if output["issues"]:
        st.dataframe(pd.DataFrame(output["issues"]), hide_index=True, width="stretch")
    else:
        st.write("None.")

    down_csv, down_json = st.columns(2)
    down_csv.download_button("Download records CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv")
    down_json.download_button("Download full JSON", json_path.read_bytes(), file_name=json_path.name, mime="application/json")


if __name__ == "__main__":
    main()
