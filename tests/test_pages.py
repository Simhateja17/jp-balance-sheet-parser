from pathlib import Path

import pytest

from bsparser.pages import find_balance_sheet_pages

ROOT = Path(__file__).parent.parent
HELDOUT = ROOT / "data" / "heldout"


@pytest.mark.parametrize("name,offered", [
    ("140120260416505142.pdf", [6]),
    ("140120260513529466.pdf", [7]),
    ("140120260514535920.pdf", [6]),
    ("tanshin202603.pdf", [5, 14]),  # consolidated and parent-only balance sheets
])
def test_only_pages_with_a_title_an_assets_part_and_a_total_assets_line_are_offered(name, offered):
    assert sorted(c.page for c in find_balance_sheet_pages(HELDOUT / name)) == offered


def test_each_offered_page_shows_a_heading_that_tells_consolidated_from_parent_only():
    bank = {c.page: c.heading for c in find_balance_sheet_pages(HELDOUT / "tanshin202603.pdf")}
    assert "連結貸借対照表" in bank[5] and "個別" not in bank[5]
    assert "個別財務諸表" in bank[14] and "貸借対照表" in bank[14]


def test_the_loose_list_is_still_available_for_the_my_page_isnt_listed_escape():
    loose = find_balance_sheet_pages(HELDOUT / "140120260416505142.pdf", strict=False)
    assert {6, 7, 11}.issubset({c.page for c in loose}) and len(loose) > 1


def test_a_page_renders_to_png_bytes_with_a_sensible_size_and_a_bad_page_is_an_error_not_an_image():
    import struct

    from bsparser.pages import render_page_png

    png = render_page_png(HELDOUT / "tanshin202603.pdf", 5, dpi=60)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", png[16:24])
    assert 300 < width < 600 and 400 < height < 800  # A4 at 60 dpi is about 496 x 702
    with pytest.raises(ValueError):
        render_page_png(HELDOUT / "tanshin202603.pdf", 999)


FRESH = ROOT / "data" / "fresh"


def test_summary_tables_titled_financial_position_are_not_offered_as_balance_sheets():
    assert [c.page for c in find_balance_sheet_pages(FRESH / "vg1mvt19a00h4bsv.pdf")] == [15]  # not the summary pages 1 and 3
    assert [c.page for c in find_balance_sheet_pages(FRESH / "ir_202603tanshin-en.pdf")] == [9]
    assert [c.page for c in find_balance_sheet_pages(FRESH / "140120260508520388.pdf")] == [8]


def test_a_statement_of_financial_position_is_still_a_balance_sheet_but_a_summary_heading_is_not(tmp_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path = tmp_path / "ifrs.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(60, 780, "Consolidated Statements of Financial Position")
    c.drawString(60, 760, "Assets")
    c.drawString(60, 740, "Total assets 7,534,110 5,135,249 Cash 2,002,429 608,281")
    c.showPage()
    c.drawString(60, 780, "(2) Consolidated financial position")
    c.drawString(60, 760, "Total assets   Net assets   Equity-to-asset ratio")
    c.drawString(60, 740, "Total assets 7,534,110 Net assets 2,002,429")
    c.save()
    assert [p.page for p in find_balance_sheet_pages(path)] == [1]
