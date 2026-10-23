import json
import subprocess
from pathlib import Path

from bsparser.pipeline import parse_with_fallback

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"
CLEAN_PDF = FIXTURES / "english_balance_sheet.pdf"


def canned_reply():
    data = json.loads((FIXTURES / "english_balance_sheet.json").read_text(encoding="utf-8"))
    return {
        "header": [f"({data['unit_raw']})", "(Mar. 31, 2025) (Mar. 31, 2026)"],
        "rows": [{"label": r["label"], "depth": r["depth"],
                  "amounts": [v["raw"] for v in r["values"]] if r["values"] else []} for r in data["rows"]],
    }


def make_scan(tmp_path):
    """An image-only PDF: the clean fixture page rendered to a picture, with no text layer."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    stem = tmp_path / "page"
    subprocess.run(["pdftoppm", "-r", "110", "-png", "-singlefile", str(CLEAN_PDF), str(stem)], check=True)
    scan = tmp_path / "scan.pdf"
    c = canvas.Canvas(str(scan), pagesize=A4)
    c.drawImage(f"{stem}.png", 0, 0, width=A4[0], height=A4[1])
    c.save()
    return scan


def test_a_clean_text_page_never_calls_the_vision_model():
    calls = []
    out = parse_with_fallback(CLEAN_PDF, runner=lambda cmd: calls.append(cmd))
    assert calls == []
    assert out["extractor"] == "text" and out["status"] == "ok"
    assert "alternative" not in out


def test_an_image_only_scan_has_no_text_records_and_is_routed_to_vision(tmp_path):
    scan = make_scan(tmp_path)
    calls = []

    def fake_runner(cmd):
        calls.append(cmd)
        return json.dumps(canned_reply(), ensure_ascii=False)

    out = parse_with_fallback(scan, runner=fake_runner)
    assert len(calls) == 1
    assert out["extractor"] == "vision" and out["status"] == "ok"
    assert len(out["records"]) == 74 and len(out["checks"]) == 20
    assert out["alternative"]["extractor"] == "text" and out["alternative"]["records"] == []
    assert any("no usable text layer" in i["message"] for i in out["issues"])
