"""Try the balance sheet parser: drop in a PDF, see the table, status, checks and issues, download the CSV.

Run: .venv/bin/streamlit run app.py   (the parser in src/bsparser is used as is)
"""
import sys
import tempfile
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pdfplumber  # noqa: E402

from bsparser.analyse import analyse, analyse_statement  # noqa: E402
from bsparser.output import write_outputs, write_statement_outputs  # noqa: E402
from bsparser.pages import Candidate, extract_page, find_balance_sheet_pages  # noqa: E402,F401


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


def show_page(st, pd, output: dict) -> None:
    """Unit, periods, table, checks and issues of one parsed page."""
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

    choice = st.selectbox("Rounding of the printed amounts (sets the tolerance of the checks)",
                          ["auto (from the cover page)", "round", "cut", "unstated"])
    rounding = "auto" if choice.startswith("auto") else choice
    whole = st.checkbox("Also read the following pages of this statement (liabilities, net assets) and check across pages",
                        value=True)
    statement = analyse_statement(source, page=page, rounding=rounding) if whole else None
    pages = statement["pages"] if statement else [analyse(source, page=page, rounding=rounding)]
    first = pages[0]
    named = work / f"{Path(upload.name).stem}_p{page}.pdf"  # only its name is used, for the downloads
    if len(pages) > 1:
        json_path, csv_path = write_statement_outputs({**statement, "source": str(named)}, work / "out")
    else:
        json_path, csv_path = write_outputs(named, work / "out", output=first)

    origin = {"cover_sentence": "from the cover sentence", "user": "chosen by you", "unstated": "not stated"}
    st.info(f"Rounding: {first['rounding']} ({first['rounding_source']}, {origin[first['rounding_source']]}). "
            f"{first['rounding_sentence'] or first['rounding_note']}")

    status = statement["status"] if statement else first["status"]
    st.subheader(f"Status: {status}")
    {"ok": st.success, "failed": st.error, "unreadable": st.warning}[status](STATUS_TEXT[status])

    if len(pages) == 1:
        show_page(st, pd, first)
    else:
        for output in pages:
            st.markdown(f"### Page {output['page']}")
            st.caption(f"Page status: {output['status']}")
            show_page(st, pd, output)
        st.subheader(f"Cross-page checks ({len(statement['cross_checks'])})")
        shown = pd.DataFrame(statement["cross_checks"])
        shown.insert(0, "result", shown.pop("status").map({"pass": "pass", "failed": "FAILED", "skipped": "skipped"}))
        st.dataframe(shown, hide_index=True, width="stretch")

    down_csv, down_json = st.columns(2)
    down_csv.download_button("Download records CSV", csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv")
    down_json.download_button("Download full JSON", json_path.read_bytes(), file_name=json_path.name, mime="application/json")


if __name__ == "__main__":
    main()
