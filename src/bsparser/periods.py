import re
from typing import List

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
ENGLISH_DATE = re.compile(r"\b([A-Za-z]{3})[a-z]*\.? (\d{1,2}), (\d{4})\b")


def find_periods(text: str) -> List[str]:
    """ISO dates in the order they are printed, e.g. 'Mar. 31, 2025' -> '2025-03-31'."""
    found = []
    for month, day, year in ENGLISH_DATE.findall(text):
        number = MONTHS.get(month.lower())
        if number:
            found.append(f"{int(year):04d}-{number:02d}-{int(day):02d}")
    return found
