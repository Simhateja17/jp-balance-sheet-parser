### Japanese page: 74 gold cells, page status ok

| slice | parser (value + role) | parser (value only) | first-match baseline (value only) | parser silent errors | parser flagged errors |
|---|---|---|---|---|---|
| all | 74 of 74 (100%) | 74 of 74 (100%) | 60 of 74 (81%) | 0 of 74 (0%) | 0 of 74 (0%) |
| repeated labels | 20 of 20 (100%) | 20 of 20 (100%) | 6 of 20 (30%) | 0 of 20 (0%) | 0 of 20 (0%) |
| nil and zero-with-mark | 3 of 3 (100%) | 3 of 3 (100%) | 3 of 3 (100%) | 0 of 3 (0%) | 0 of 3 (0%) |
| net and contra | 16 of 16 (100%) | 16 of 16 (100%) | 10 of 16 (62%) | 0 of 16 (0%) | 0 of 16 (0%) |

Gold values pass the accounting identities: 20 of 20

first-match baseline errors: 14 of 74
- 資産の部/固定資産/有形固定資産/機械装置及び運搬具 / 減価償却累計額 / 2025-03-31 / gold △3,634,165
- 資産の部/固定資産/有形固定資産/機械装置及び運搬具 / 減価償却累計額 / 2026-03-31 / gold △1,914,091
- 資産の部/固定資産/有形固定資産/リース資産 / 減価償却累計額 / 2025-03-31 / gold △147,599
- 資産の部/固定資産/有形固定資産/リース資産 / 減価償却累計額 / 2026-03-31 / gold △172,066
- 資産の部/固定資産/有形固定資産 / その他 / 2025-03-31 / gold 848,814
- 資産の部/固定資産/有形固定資産 / その他 / 2026-03-31 / gold 446,126
- 資産の部/固定資産/有形固定資産/その他 / 減価償却累計額 / 2025-03-31 / gold △840,375
- 資産の部/固定資産/有形固定資産/その他 / 減価償却累計額 / 2026-03-31 / gold △421,883
- 資産の部/固定資産/無形固定資産 / リース資産 / 2025-03-31 / gold 34,190
- 資産の部/固定資産/無形固定資産 / リース資産 / 2026-03-31 / gold 21,402
- 資産の部/固定資産/無形固定資産 / その他 / 2025-03-31 / gold 10,070
- 資産の部/固定資産/無形固定資産 / その他 / 2026-03-31 / gold 14,466
- 資産の部/固定資産/投資その他の資産 / その他 / 2025-03-31 / gold 133,361
- 資産の部/固定資産/投資その他の資産 / その他 / 2026-03-31 / gold 70,967

Limits:
- Gold values were read from the page image by a separate Claude session, not by a human, and not from the text layer or the parser. A reading error shared by two models is possible.
- The parser rules were developed on this same page, so a perfect score here is in-sample. It is not evidence about other filings. Held-out layouts (messy English variant, other filings) are still to be measured.
- The baseline is a deliberately naive lookup: first line with the same label, section path ignored.
- Gold is compared as printed text. The parser's own sign and nil rules are covered by separate unit tests.
