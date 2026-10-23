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
