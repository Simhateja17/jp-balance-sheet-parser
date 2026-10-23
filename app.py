"""Try the balance sheet parser: drop in a PDF, see the table, status, checks and issues, download the CSV.

Run: .venv/bin/streamlit run app.py   (the parser in src/bsparser is used as is)
"""
import sys
import tempfile
import traceback
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pdfplumber  # noqa: E402

from bsparser.analyse import analyse, analyse_statement  # noqa: E402
from bsparser.output import write_outputs, write_statement_outputs  # noqa: E402
from bsparser.pages import Candidate, extract_page, find_balance_sheet_pages  # noqa: E402,F401


def failed_rows(output: dict, cross_checks: List[dict] = None) -> dict:
    """Rows that belong to a FAILED check (the printed total and what it adds up), with why. Skipped and passing
    checks mark nothing. A failed cross-page check marks its totals on their own page."""
    why: dict = {}
    for check in output["checks"]:
        if check["status"] != "failed":
            continue
        text = (f"{check['label']} {check['period']}: printed {check['printed']}, adds up to {check['expected']}, "
                f"off by {check['difference']} (allowed {check['bound']})")
        for row_id in check.get("row_ids", []):
            why.setdefault(row_id, []).append(text)
    for check in cross_checks or []:
        if check["status"] != "failed":
            continue
        text = (f"{check['label']} {check['period']}: printed {check['printed']}, expected {check['expected']}, "
                f"off by {check['difference']} (allowed {check['bound']})")
        for ref in check.get("rows", []):
            if ref["page"] == output.get("page"):
                why.setdefault(ref["row_id"], []).append(text)
    return why


def table_rows(output: dict, why: dict = None) -> List[dict]:
    """One display row per table row: indented label, English reading label, role, the printed value per period,
    and, for rows in a failed check, why."""
    why = why or {}
    raw = {(r["id"].split("|")[0], r["period"]): r["raw"] for r in output["records"]}
    rows = []
    for row in output["rows"]:
        line = {"label": "\u00a0\u00a0\u00a0" * row["level"] + row["label"], "label_en": row["label_en"] or "", "role": row["role"]}
        for period in output["periods"]:
            line[period] = raw.get((row["id"], period), "")
        line["why"] = " | ".join(why.get(row["id"], []))
        rows.append(line)
    return rows


def styled_table(rows: List[dict]):
    """The table with a red background on every row that belongs to a failed check."""
    import pandas as pd

    frame = pd.DataFrame(rows)
    return frame.style.apply(
        lambda row: ["background-color: #fde2e2" if row["why"] else ""] * len(row), axis=1)


STATUS_TEXT = {
    "ok": "Everything adds up, within the rounding tolerance.",
    "failed": "Some numbers do not add up. The rows in red are the ones involved: compare them with the page image.",
    "unreadable": "Part of this page could not be read (a value, the unit, the periods or a column). The issues below say what.",
}

FRIENDLY = {
    "open": "We couldn't open this file as a PDF. Check that it really is a PDF (not a renamed picture or a damaged "
            "download) and try again.",
    "scan": "This PDF has no text layer: it looks scanned, so its pages are pictures. This page reads the text layer "
            "only, so it can't read them. A vision model could, but that fallback is not available here.",
    "no_page": "No page looks like a balance sheet (none has a balance sheet title, an assets part and a total-assets "
               "line). Open \"My page isn't listed\" below and type a page number to try one anyway.",
    "went_wrong": "Something went wrong while reading page {page}. Nothing was changed. Try another page or another "
                  "rounding option, or open the technical details below to see what happened.",
    "no_rows": "No table was found on this page. It may not be a balance sheet, or the page may be a picture. "
               "Try another page from the list.",
}


def show_page(st, pd, output: dict) -> None:
    """Unit, periods, table, checks and issues of one parsed page."""
    left, mid, right = st.columns(3)
    left.metric("Unit", f"{output['unit'] or 'not found'}", output["unit_raw"] or None)
    mid.metric("Periods", ", ".join(output["periods"]) or "not found")
    right.metric("Rows / records", f"{len(output['rows'])} / {len(output['records'])}")

    if not output["rows"]:
        st.info(FRIENDLY["no_rows"])
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
    try:
        with pdfplumber.open(source) as pdf:
            total_pages = len(pdf.pages)
            has_text = any((page.extract_text() or "").strip() for page in pdf.pages)
    except Exception:  # noqa: BLE001 - a file we cannot open is a message, not a traceback
        st.warning(FRIENDLY["open"])
        return
    if not has_text:
        st.warning(FRIENDLY["scan"])
        return

    candidates = find_balance_sheet_pages(source)
    chosen = None
    if candidates:
        labels = [f"page {c.page}: {c.heading or c.reason}" for c in candidates]
        pick = st.selectbox(f"{total_pages} pages. Balance sheets found, best first", labels)
        chosen = candidates[labels.index(pick)].page
    with st.expander("My page isn't listed", expanded=not candidates):
        manual = int(st.number_input("Use this page instead (0 = the one chosen above)", min_value=0,
                                     max_value=total_pages, value=0, step=1))
    page = manual or chosen
    if page is None:
        st.info(FRIENDLY["no_page"])
        return

    choice = st.selectbox("Rounding of the printed amounts (sets the tolerance of the checks)",
                          ["auto (from the cover page)", "round", "cut", "unstated"])
    rounding = "auto" if choice.startswith("auto") else choice
    whole = st.checkbox("Also read the following pages of this statement (liabilities, net assets) and check across pages",
                        value=True)
    try:
        statement = analyse_statement(source, page=page, rounding=rounding) if whole else None
        pages = statement["pages"] if statement else [analyse(source, page=page, rounding=rounding)]
        first = pages[0]
        named = work / f"{Path(upload.name).stem}_p{page}.pdf"  # only its name is used, for the downloads
        if len(pages) > 1:
            json_path, csv_path = write_statement_outputs({**statement, "source": str(named)}, work / "out")
        else:
            json_path, csv_path = write_outputs(named, work / "out", output=first)
    except Exception:  # noqa: BLE001 - plain words for the user, the detail tucked away
        st.warning(FRIENDLY["went_wrong"].format(page=page))
        with st.expander("Technical details"):
            st.code(traceback.format_exc())
        return

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
