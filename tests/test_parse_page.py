from pathlib import Path

from bsparser.page import parse_page

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def test_parse_page_returns_the_43_table_rows_without_the_header_block():
    page = parse_page(FIXTURE_PDF)
    assert len(page.rows) == 43
    assert page.rows[0].label == "Assets"
    assert page.rows[-1].label == "Total assets"


def test_contra_row_has_role_level_and_a_path_through_its_gross_item():
    page = parse_page(FIXTURE_PDF)
    contra = [r for r in page.rows if r.label == "Accumulated depreciation"][0]
    assert contra.role == "contra"
    assert contra.path == [
        "Assets",
        "Non-current assets",
        "Property, plant and equipment",
        "Buildings and structures",
    ]


def test_contra_and_net_rows_point_to_the_gross_row_and_others_have_no_parent():
    page = parse_page(FIXTURE_PDF)
    by_id = {r.id: r for r in page.rows}
    assert [r.id for r in page.rows][:3] == ["r1", "r2", "r3"]
    gross = [r for r in page.rows if r.label == "Buildings and structures"][0]
    contra = [r for r in page.rows if r.label == "Accumulated depreciation"][0]
    net = [r for r in page.rows if r.label == "Buildings and structures, net"][0]
    assert contra.parent == gross.id
    assert net.parent == gross.id
    assert by_id[net.parent].label == "Buildings and structures"
    assert all(r.parent is None for r in page.rows if r.role not in ("contra", "net"))
