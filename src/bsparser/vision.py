from typing import Dict, List

from bsparser.pdf_lines import Line

LEFT, STEP, LINE_HEIGHT = 60.0, 12.0, 14.0  # synthetic geometry: the model gives depth, not pixels


def lines_from_vision(reply: Dict) -> List[Line]:
    """Turn a vision reply into the same Line objects the text parser makes, so roles, checks and status are shared."""
    lines = [Line(text, LEFT, i * LINE_HEIGHT) for i, text in enumerate(reply["header"])]
    top = len(lines) * LINE_HEIGHT
    for row in reply["rows"]:
        lines.append(Line(row["label"], LEFT + STEP * row["depth"], top, list(row["amounts"])))
        top += LINE_HEIGHT
    return lines


import json


def extract_reply(text: str) -> Dict:
    """The JSON object in a model reply, with or without chatter or code fences. Wrong shape is an error."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the vision reply")
    try:
        reply = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"vision reply is not valid JSON: {exc}") from exc
    if not isinstance(reply.get("header"), list) or not isinstance(reply.get("rows"), list):
        raise ValueError("vision reply needs 'header' (list) and 'rows' (list)")
    return reply


import subprocess
import tempfile
from pathlib import Path

PROMPT = """Read the image file {png} (one page of a financial statement) and transcribe its table.
Return ONLY one JSON object, no other text:
{{"header": [<each text line above the table: unit line, period column headings>],
  "rows": [{{"label": <label exactly as printed>, "depth": <indent level, 0 for the leftmost labels>,
            "amounts": [<one string per period column exactly as printed, [] when the line has no numbers>]}}]}}
Rules: copy every number exactly as printed, including marks such as a triangle, brackets, minus signs and dashes.
A dash alone is a printed nil: keep it as the dash. Keep full-width characters as they are.
A label wrapped over two lines is one row (join the two lines; the numbers belong to it).
Keep every line in page order, including section headers with no numbers and totals.
Do not add, fix or compute any value, and do not skip a line you cannot read: copy what you see."""


def _claude_runner(cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True).stdout


def run_vision(pdf_path, runner=_claude_runner, dpi: int = 150) -> Dict:
    """Render page 1 to a PNG and ask headless Claude Code (Read tool only) to transcribe it.
    Prototype: production would call an API or a fine-tuned model."""
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "page"
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", "1", "-l", "1", "-png", "-singlefile", str(pdf_path), str(stem)],
                       check=True, capture_output=True)
        png = f"{stem}.png"
        cmd = ["claude", "-p", "--allowedTools", "Read", "--add-dir", tmp, PROMPT.format(png=png)]
        return extract_reply(runner(cmd))
