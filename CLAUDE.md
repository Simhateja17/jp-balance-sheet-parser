# Balance sheet parser (Ur AI take-home)

Goal: turn one page of a financial statement into a correct table, English first, then Japanese.
Deadline: Sun 25 Oct 2026, 11:59 pm IST. The full AI chat log is part of the submission (`/export` into docs/ai-log/).

## How we work
- Before building anything new, interview me about it: one question at a time, each with your recommended answer. Do not ask what you can find in the repo. No code until I say the spec is agreed.
- Record agreed decisions in docs/decisions.md.
- Build in vertical slices: ONE failing test, then the minimal code to pass it, then the next. Never write all tests up front.
- Run tests after every change and show the real output. Never edit a test to make it pass; fix the source.
- Commit after each green step with a clear message (`test:`, `feat:`, `fix:`).
- After each step, say in two lines what changed and what is next. Short, plain language.
- If you are unsure of a number or a rule, say so. Never guess a value.

## Domain rules (never break)
- Nil ("-", "—", "－") is None, never 0.
- Negatives: "(1,234)" and "-1,234" in English, "△1,234" in Japanese. "△0" is 0.
- Same label can appear in several sections (その他, リース資産, 減価償却累計額). Always keep the section path.
- Verify with accounting identities: items sum to the subtotal (allow a few units of rounding, report the difference), gross + accumulated depreciation = net, current + fixed = total assets.
- Never silently drop or guess a value. Record a warning.

## Phases
1. English text: tokens, rows, sections, roles
2. English PDF: extraction, messy layout (fake PDFs with known answers first, then one real filing)
3. Japanese: unit 千円, △, －, repeated labels, （純額）
4. Evaluate: identity checks, hand-written gold Q&A, naive first-match baseline, report

## Commands
- Install: `pip install -r requirements.txt`
- Test: `python -m pytest -q --tb=short`
- Layout: src/parser/, tests/, data/, docs/, outputs/

## Style
Short and dense. No em dashes in any written text.
