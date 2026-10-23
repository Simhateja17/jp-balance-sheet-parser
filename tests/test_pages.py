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
