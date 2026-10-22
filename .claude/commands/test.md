---
description: Run the pytest suite and fix any failures
argument-hint: "[path or -k expression]"
allowed-tools: Bash(python -m pytest:*)
---

Run `python -m pytest -q --tb=short $ARGUMENTS`.

If a test fails, read the traceback and fix the cause in the source. Never edit a
test to make it pass. Rerun with `--last-failed` until the suite is green, then
show me the final output.
