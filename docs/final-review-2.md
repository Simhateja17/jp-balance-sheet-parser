# Final review 2: balance_sheet_after_correction (final records vs page image)

Reviewer: independent session. Compared outputs/balance_sheet_after_correction.records.csv (74 records, 37 rows x 2 periods) against the image of data/balance_sheet_after_correction.pdf, page 1 (same file as review 1, sha1 5d0a5d15...). Parser code and tests not read.

Method: transcribed every printed cell from the image, then diffed raw text and value for all 74 records by script; checked label, path and role by eye.

## Disagreements

| record | field | output | image / template | note |
|--------|-------|--------|------------------|------|
| r12 (both periods) | role | item | contra in the gold template | 貸倒引当金 (allowance for doubtful accounts), printed with △ both years. Value and sign correct. Unchanged since review 1. |

No disagreement in any value, sign, nil, raw text, label or section path. No record missing, none extra.
