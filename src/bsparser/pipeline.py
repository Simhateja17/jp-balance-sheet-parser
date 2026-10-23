from typing import Dict

from bsparser.arbitrate import arbitrate
from bsparser.output import build_output, output_from_page
from bsparser.page import parse_lines
from bsparser.vision import _claude_runner, lines_from_vision, run_vision


def parse_with_fallback(pdf_path, runner=_claude_runner) -> Dict:
    """D7 routing. Text first. Only a page with no usable text, or whose identity checks fail, goes to vision.
    The same checks judge both outputs."""
    text = build_output(pdf_path)
    needs_vision = not text["records"] or text["status"] != "ok"
    if not needs_vision:
        text["extractor"] = "text"
        return text
    reply = run_vision(pdf_path, runner=runner)
    vision = output_from_page(parse_lines(lines_from_vision(reply)), str(pdf_path))
    return arbitrate(text=text, vision=vision)
