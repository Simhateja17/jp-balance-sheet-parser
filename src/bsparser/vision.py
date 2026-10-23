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
