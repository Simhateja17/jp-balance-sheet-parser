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


if __name__ == "__main__":
    render(json.loads(DATA.read_text(encoding="utf-8")), DATA.with_suffix(".pdf"))
