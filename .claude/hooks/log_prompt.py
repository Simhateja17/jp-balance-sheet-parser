#!/usr/bin/env python3
"""UserPromptSubmit hook: append every prompt, verbatim, to docs/prompts.md."""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    data = json.load(sys.stdin)
    prompt = data.get("prompt", "").strip()
    if prompt:
        root = Path(data.get("cwd") or ".")
        out = root / "docs" / "prompts.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists():
            out.write_text("# Prompts I sent (verbatim, in order)\n\n", encoding="utf-8")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with out.open("a", encoding="utf-8") as f:
            f.write(f"## {stamp}\n\n```\n{prompt}\n```\n\n")
except Exception:
    pass  # never block the session because logging failed
sys.exit(0)
