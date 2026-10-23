import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))  # app.py sits at the repo root

from app import extract_page, find_balance_sheet_pages  # noqa: E402

REAL_PDF = ROOT / "data" / "balance_sheet_after_correction.pdf"
ENGLISH_PDF = ROOT / "data" / "fixtures" / "english_balance_sheet.pdf"


def three_page_pdf(tmp_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path = tmp_path / "report.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(60, 780, "Annual report 2025. Message from the chairman.")
    c.showPage()
    c.drawString(60, 780, "Consolidated balance sheet (in thousands of yen)")
    c.drawString(60, 760, "Total assets 7,534,110 5,135,249 Cash 2,002,429 608,281")
    c.showPage()
    c.drawString(60, 780, "Consolidated statements of cash flows 1,000 2,000")
    c.save()
    return path


def test_the_balance_sheet_page_is_found_in_a_longer_document_and_ranked_first(tmp_path):
    candidates = find_balance_sheet_pages(three_page_pdf(tmp_path))
    assert candidates[0].page == 2
    assert "balance sheet" in candidates[0].reason.lower()
    assert [c.page for c in candidates][0] == 2


def test_real_japanese_and_english_pages_are_found_on_page_one():
    assert find_balance_sheet_pages(REAL_PDF)[0].page == 1
    assert find_balance_sheet_pages(ENGLISH_PDF)[0].page == 1


def test_a_document_with_no_balance_sheet_gives_no_candidates(tmp_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path = tmp_path / "other.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(60, 780, "Meeting minutes. Agenda item one.")
    c.save()
    assert find_balance_sheet_pages(path) == []


def test_extract_page_writes_a_one_page_pdf_with_that_pages_text(tmp_path):
    import pdfplumber

    out = extract_page(three_page_pdf(tmp_path), 2, tmp_path / "page2.pdf")
    with pdfplumber.open(out) as pdf:
        assert len(pdf.pages) == 1
        assert "Total assets" in pdf.pages[0].extract_text()


def test_table_rows_show_indented_labels_english_reading_and_the_printed_value_per_period():
    from app import table_rows
    from bsparser.output import build_output

    rows = table_rows(build_output(REAL_PDF))
    assert len(rows) == 43
    header, cash, nil_row = rows[1], rows[2], [r for r in rows if r["label"].strip() == "建設仮勘定"][0]
    assert header["label"] == "   流動資産" and header["2025-03-31"] == "" and header["role"] == "header"
    assert (cash["label_en"], cash["role"], cash["2025-03-31"], cash["2026-03-31"]) == (
        "Cash and deposits", "item", "2,002,429", "608,281")
    assert nil_row["2025-03-31"] == "－" and nil_row["2026-03-31"] == "4,553"  # the printed dash, not a 0


def test_the_page_renders_status_table_checks_and_downloads_for_an_uploaded_pdf():
    from streamlit.testing.v1 import AppTest

    def script(pdf_path):
        import sys
        from pathlib import Path

        import streamlit as st

        sys.path.insert(0, str(Path(pdf_path).parent.parent))
        import app

        class Upload:
            name = Path(pdf_path).name

            def getvalue(self):
                return Path(pdf_path).read_bytes()

        st.file_uploader = lambda *args, **kwargs: Upload()
        app.main()

    at = AppTest.from_function(script, args=(str(REAL_PDF),), default_timeout=60).run()
    assert not at.exception
    assert [s.value for s in at.subheader][:1] == ["Status: ok"]
    assert at.success[0].value.startswith("ok:")
    assert len(at.dataframe) == 3  # table, checks, and the issues table (the printed page number is one issue)
    assert len(at.get("download_button")) == 2  # records CSV and full JSON


HELDOUT_4098 = ROOT / "data" / "heldout" / "140120260416505142.pdf"


def _app_for(pdf_path):
    from streamlit.testing.v1 import AppTest

    def script(pdf_path):
        import sys
        from pathlib import Path

        import streamlit as st

        sys.path.insert(0, str(Path(pdf_path).parent.parent.parent))
        import app

        class Upload:
            name = Path(pdf_path).name

            def getvalue(self):
                return Path(pdf_path).read_bytes()

        st.file_uploader = lambda *args, **kwargs: Upload()
        app.main()

    return AppTest.from_function(script, args=(str(pdf_path),), default_timeout=90)


def test_the_page_shows_the_rounding_hint_and_lets_the_user_override_it_and_records_that():
    at = _app_for(HELDOUT_4098).run()
    assert not at.exception
    rounding = [m.value for m in at.info if m.value.startswith("Rounding:")]
    assert len(rounding) == 1 and "cut" in rounding[0] and "cover_sentence" in rounding[0]
    assert "百万円未満切捨て" in rounding[0]
    assert at.subheader[0].value == "Status: ok"  # 4098 passes under the cover's cut-off bound
    options = at.selectbox[1].options
    assert options[0].startswith("auto") and set(options[1:]) == {"round", "cut", "unstated"}
    at.selectbox[1].select("round").run()
    chosen = [m.value for m in at.info if m.value.startswith("Rounding:")][0]
    assert "round" in chosen and "chosen by you" in chosen
    assert at.subheader[0].value == "Status: failed"  # the strict bound fails the cut-off difference of 5


def test_statement_mode_shows_every_page_a_cross_page_table_and_the_statement_status():
    at = _app_for(HELDOUT_4098).run()
    assert not at.exception
    assert at.subheader[0].value == "Status: ok"  # the statement status
    page_headers = [h.value for h in at.markdown if h.value.startswith("### Page ")]
    assert page_headers == ["### Page 6", "### Page 7"]
    cross = [s.value for s in at.subheader if s.value.startswith("Cross-page checks")]
    assert cross == ["Cross-page checks (4)"]
    assert len(at.get("download_button")) == 2
    checkbox = at.checkbox[0]
    assert checkbox.value is True
    checkbox.uncheck().run()
    assert [h.value for h in at.markdown if h.value.startswith("### Page ")] == []  # single page: no page headers
    assert not [s for s in at.subheader if s.value.startswith("Cross-page checks")]


def failing_output(total_prior="602"):
    from bsparser.output import output_from_page
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    page = parse_lines([
        Line("(in thousands of yen)", 400.0, 70.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Current assets", 72.0, 134.0),
        Line("Cash", 84.0, 148.0, ["100", "100"]),
        Line("Notes receivable", 84.0, 162.0, ["200", "200"]),
        Line("Other", 84.0, 176.0, ["300", "300"]),
        Line("Total current assets", 84.0, 190.0, [total_prior, "600"]),  # 2025: 3 items, bound 2: 602 passes, 605 fails
        Line("Land", 72.0, 204.0, ["50", "50"]),
        Line("Total assets", 72.0, 218.0, [str(int(total_prior) + 50), "650"]),  # follows the printed subtotal plus Land
    ])
    out = output_from_page(page, "synthetic.pdf")
    out["page"] = 1
    return out


def test_rows_of_a_failed_check_are_marked_with_why_and_skipped_or_passing_checks_mark_nothing():
    from app import failed_rows, table_rows

    ok = failing_output("602")
    assert failed_rows(ok) == {}
    bad = failing_output("605")  # 605 against 600: difference 5, bound 2
    why = failed_rows(bad)
    ids = {r["label"]: r["id"] for r in bad["rows"]}
    assert set(why) == {ids["Total current assets"], ids["Cash"], ids["Notes receivable"], ids["Other"]}  # total assets passes
    assert "Total current assets" in why[ids["Cash"]][0] and "2025-03-31" in why[ids["Cash"]][0] and "5" in why[ids["Cash"]][0]
    table = table_rows(bad, why)
    by_label = {r["label"].strip(): r for r in table}
    assert by_label["Cash"]["why"].startswith("Total current assets") and by_label["Assets"]["why"] == ""
    assert by_label["Total current assets"]["why"] != ""


def test_a_failed_cross_page_check_marks_its_totals_only_on_their_own_page():
    from app import failed_rows

    out = failing_output("602")
    out["page"] = 6
    cross = [{"status": "failed", "label": "資産合計 = 負債純資産合計", "period": "2025-03-31", "printed": 101, "expected": 100,
              "difference": 1, "bound": 0, "rows": [{"page": 5, "row_id": "r23"}, {"page": 6, "row_id": "r3"}]},
             {"status": "skipped", "label": "x", "period": "2025-03-31", "printed": None, "expected": None,
              "difference": None, "bound": 0, "rows": [{"page": 6, "row_id": "r4"}]}]
    assert list(failed_rows(out, cross)) == ["r3"]  # page 6 only; page 5's row is marked on page 5; skipped marks nothing
    out["page"] = 5
    assert list(failed_rows(out, cross)) == ["r23"]


def test_the_table_is_styled_with_a_red_background_only_on_rows_that_have_a_why():
    from app import styled_table, table_rows

    bad = failing_output("605")
    from app import failed_rows

    rows = table_rows(bad, failed_rows(bad))
    html = styled_table(rows).to_html()
    marked = sum(1 for r in rows if r["why"])
    assert marked == 4
    css = html[:html.index("</style>")]
    assert css.count("background-color: #fde2e2") == marked  # one rule per marked row, covering its six cells
    import re

    coloured = sorted({int(n) for n in re.findall(r"_row(\d+)_col0", css)})
    assert coloured == [2, 3, 4, 5]  # Cash, Notes receivable, Other, Total current assets; not Land or Total assets
