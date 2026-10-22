"""Render data/fixtures/english_balance_sheet.json to a one-page PDF.

Run by hand: .venv/bin/python tests/make_english_fixture.py
The generated PDF is committed; tests do not regenerate it.
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DATA = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.json"
LEFT, INDENT, COL1, COL2, TOP, STEP = 60, 12, 420, 520, 740, 14.5


def render(data, out):
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, 790, "3. Consolidated financial statements and notes")
    c.drawString(LEFT + 8, 776, "(1) Consolidated balance sheet")
    c.drawRightString(COL2, 762, f"({data['unit_raw']})")
    c.drawRightString(COL1, TOP, "Prior fiscal year")
    c.drawRightString(COL2, TOP, "Current fiscal year")
    c.drawRightString(COL1, TOP - 11, "(Mar. 31, 2025)")
    c.drawRightString(COL2, TOP - 11, "(Mar. 31, 2026)")
    y = TOP - 30
    for row in data["rows"]:
        c.drawString(LEFT + INDENT * row["depth"], y, row["label"])
        if row["values"]:
            c.drawRightString(COL1, y, row["values"][0]["raw"])
            c.drawRightString(COL2, y, row["values"][1]["raw"])
        y -= STEP
    c.showPage()
    c.save()


WRAPPED_LABEL = "Electronically recorded monetary claims"


def render_messy(data, out):
    """Same data, messier layout: value columns shifted right of the header, small x jitter on the labels,
    and one long label wrapped over two lines (values on the second line, slightly deeper, tight spacing)."""
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, 790, "3. Consolidated financial statements and notes")
    c.drawRightString(COL2 + 20, 762, f"({data['unit_raw']})")
    c.drawRightString(COL1, TOP, "Prior fiscal year")
    c.drawRightString(COL2, TOP, "Current fiscal year")
    c.drawRightString(COL1, TOP - 11, "(Mar. 31, 2025)")
    c.drawRightString(COL2, TOP - 11, "(Mar. 31, 2026)")
    y = TOP - 30
    jitter = [0.0, 0.6, -0.5, 0.3, -0.7]
    for n, row in enumerate(data["rows"]):
        x = LEFT + INDENT * row["depth"] + jitter[n % len(jitter)]
        if row["label"] == WRAPPED_LABEL:
            first, second = "Electronically recorded monetary", "claims"
            c.drawString(x, y, first)
            y -= 8
            c.drawString(x + 6, y, second)
        else:
            c.drawString(x, y, row["label"])
        if row["values"]:
            c.drawRightString(COL1 + 15, y, row["values"][0]["raw"])
            c.drawRightString(COL2 + 15, y, row["values"][1]["raw"])
        y -= STEP
    c.showPage()
    c.save()


if __name__ == "__main__":
    data = json.loads(DATA.read_text(encoding="utf-8"))
    render(data, DATA.with_suffix(".pdf"))
    render_messy(data, DATA.with_name(DATA.stem + "_messy.pdf"))
