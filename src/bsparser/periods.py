import re
import unicodedata
from typing import List

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
ENGLISH_DATE = re.compile(r"\b([A-Za-z]{3})[a-z]*\.? (\d{1,2}), (\d{4})\b")
REIWA_DATE = re.compile(r"\u4ee4\u548c ?(\u5143|\d{1,2}) ?\u5e74 ?(\d{1,2}) ?\u6708 ?(\d{1,2}) ?\u65e5")  # 令和7年3月31日; 元 is year 1
REIWA_FIRST_YEAR = 2019
JAPANESE_DATE = re.compile(r"(\d{4}) ?\u5e74 ?(\d{1,2}) ?\u6708 ?(\d{1,2}) ?\u65e5")  # 2025年3月31日


def find_periods(text: str) -> List[str]:
    """ISO dates in the order they are printed, e.g. 'Mar. 31, 2025' -> '2025-03-31'."""
    text = unicodedata.normalize("NFKC", text)  # full-width digits and brackets to plain ones
    found = []  # (position in text, ISO date) so mixed forms keep the printed order
    for m in ENGLISH_DATE.finditer(text):
        number = MONTHS.get(m.group(1).lower())
        if number:
            found.append((m.start(), f"{int(m.group(3)):04d}-{number:02d}-{int(m.group(2)):02d}"))
    for m in JAPANESE_DATE.finditer(text):
        found.append((m.start(), f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"))
    for m in REIWA_DATE.finditer(text):
        year = 1 if m.group(1) == "\u5143" else int(m.group(1))
        found.append((m.start(), f"{REIWA_FIRST_YEAR + year - 1:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"))
    return [iso for _, iso in sorted(found)]
