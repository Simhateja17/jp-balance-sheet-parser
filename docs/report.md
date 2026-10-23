# Report: balance sheet page parser

Task: turn one page of a Japanese consolidated balance sheet (資産の部, unit 千円, two periods) into a correct table. English first, then Japanese. Full decisions: `docs/decisions.md` (D1 to D15).

## What "correct" means

Three layers, reported separately (D4):

1. **Cell exactness against gold.** The printed text of each value must match: digits, sign mark, nil (`－`) versus zero (`△0`).
2. **Structure against gold.** Each cell is keyed by (section path, label, period), never by row number, so the three 減価償却累計額 lines and the three その他 lines cannot be mixed up. The role (item, contra, net, subtotal, total) must match too.
3. **Accounting identities, no gold needed.** Items sum to their subtotal, gross plus accumulated depreciation equals net, sub-totals sum to total assets. Tolerance is strict and set up front: `floor(0.5 x (items + 1))`, because each item and the printed total are rounded. Nil items do not count (no rounding error). Above the bound is a failure, not a warning. Every check prints its difference and its bound.

Wrong-but-flagged is better than wrong-and-silent, so the report counts the two apart. Nothing is dropped or adjusted to make a sum work. A value that cannot be read stays as `unreadable` with its raw text, and any check touching it is `skipped` with a reason (D6). Page status is the worst issue: unreadable over failed over ok.

Output record (D1): one JSON record per row per period, with `id`, `path`, `label`, `label_en` (a reading translation, never used in matching or checks), `role`, `parent` (only the gross link for contra and net rows), `period`, `value` (int or None), `raw`, `unit`, `warnings`. Values stay in the printed unit.

## Results (real Japanese page, 37 value rows x 2 periods = 74 gold cells)

Parser page status: `ok`. All 20 identity checks pass, largest difference 3 (the printed rounding), and several sit exactly on their bound.

| slice | parser (value + role) | first-match baseline (value only) |
|---|---|---|
| all | 74 of 74 (100%) | 60 of 74 (81%) |
| repeated labels | 20 of 20 (100%) | 6 of 20 (30%) |
| nil and zero-with-mark | 3 of 3 (100%) | 3 of 3 (100%) |
| net and contra | 16 of 16 (100%) | 10 of 16 (62%) |

Parser silent errors: 0 of 74. Flagged errors: 0 of 74. The gold values themselves pass 20 of 20 identity checks, so a single mistyped gold value is unlikely (two errors that cancel out would not be caught). Raw table: `outputs/accuracy_japanese.md`.

Other checks (no gold, structure only): the English fixture and the real Japanese page produce the same row count, roles, depth, parent links and values (parity test, D5). A messy English variant (shifted columns, x jitter, one wrapped label) parses like the clean one with one `wrapped_label_merged` issue. The English fixture's "gold" is its own source data, so it only shows nothing broke. It is not an accuracy measure.

## Why the baseline loses on repeated labels

The baseline is deliberately naive: take the first line whose label matches, ignore the section, take the number in the column. It is exact on every unique label. All 14 of its errors are repeated labels after the first: その他 appears under current assets, tangible assets, intangible assets and investments; リース資産 under tangible and intangible; 減価償却累計額 under three gross items. First-match returns the first occurrence's number for every later one. The parser keeps the section path (from indentation levels clustered per page) and links each contra and net row to its gross row, so the same label in a different place is a different cell.

The baseline is also tied to this layout: it reads the same text lines as the parser. The gap measures structure handling only, not extraction quality.

## Honest limits

- **Gold is not fully independent.** The gold values were read from the page image by a separate Claude chat, not by a human. That chat had already seen this page's text through Google Drive earlier (as reported by the project owner), so its reading is not independent of the text layer the parser reads. A shared misreading is possible. Partial mitigation: the gold passes all 20 accounting identities.
- **Nobody who reads Japanese checked anything.** The labels in the gold template were transcribed by Claude and then checked by another Claude session against the image (`docs/label-check.md`). The English translations were written by Claude and checked by the same reviewer session (`docs/translation-check.md`). No human reader of Japanese has verified the labels, the translations, or the gold. The owner does not read Japanese.
- **The page is in-sample.** Every parser rule was developed against this one page, so 100% here is not evidence about other filings. The messy English variant is a held-out layout, but I built it myself. Real held-out filings are the missing test.
- **Comparison is on printed text.** The parser's own sign and nil rules are covered by unit tests, not by gold. A wrong rule that also appears in the gold typing would not be caught.
- **Scope.** One page, text-layer PDF, assets half only. Out of scope and flagged where cheap: multi-page tables, liabilities and equity on another page, other statements, merged cells. Eras other than Reiwa are flagged, not converted. A Japanese label missing from the translation dictionary gets `label_en: null` and a warning.
- **Strict tolerance can hide real errors** of one or two units on small sections. It is reported with every check so the reader can see the margin.

## Scanned pages and the vision fallback (design, D7)

This PDF has a text layer, so no OCR or vision model is used on it. For pages that do not:

1. **Route.** If a page has no usable text layer (no words, or words that do not parse into a table), or the identity checks fail, send the page image to a vision fallback.
2. **Same schema.** The vision model must return the same JSON rows and records (D1). Nothing downstream changes.
3. **Same judge.** The same identity checks, status rules and warnings judge the vision output. The checks are the confidence signal for any extractor, text or vision.
4. **Arbitration when both run.** Fewer failed checks wins, any `unreadable` counts against, a tie goes to text, no cell-by-cell merging. Both outputs are kept. Every cell where the two disagree is flagged, even when both pass, because two swapped rows in a section keep every sum intact, so agreement between extractors is extra evidence. If both fail, the text output is returned as `failed` with the vision output attached.
5. **Prototype status and production.** The prototype uses Claude Code in headless mode because no API key was available. Production would use an API model or a fine-tuned model, with the identity checks as the filter and gold-based evaluation as the measure. Passing identities is a signal, not proof: a model can produce numbers that sum correctly and are still wrong, so gold stays the real measure.

(Prototype results are added below once it is built.)
