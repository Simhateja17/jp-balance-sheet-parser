from typing import Dict, List, Optional

from bsparser.checks import bound_for
from bsparser.totals import kind_of_total

A_LABEL = "total assets = total liabilities and net assets"
B_LABEL = "total liabilities and net assets = total liabilities + total net assets"


def _find(pages: List[Dict], kind: str, period: str) -> Optional[Dict]:
    for page in pages:
        for rec in page["records"]:
            if rec["period"] == period and kind_of_total(rec["label"]) == kind:
                return {**rec, "_page": page.get("page")}
    return None


def _ref(rec: Optional[Dict]) -> List[Dict]:
    """Where a total sits, so a failed check can be highlighted on its page."""
    if rec is None:
        return []
    return [{"page": rec["_page"], "row_id": rec.get("id", "").split("|")[0]}]


def _skipped(label: str, period: str, reason: str, rows: Optional[List[Dict]] = None) -> Dict:
    return {"label": label, "period": period, "expected": None, "printed": None, "difference": None,
            "bound": 0, "items": 0, "status": "skipped", "reason": reason, "rows": rows or []}


def _usable(rec: Optional[Dict], name: str) -> Optional[str]:
    """None when the record can be used; otherwise the reason it cannot."""
    if rec is None:
        return f"{name} not found on any page"
    if rec["kind"] == "unreadable":
        return f"{name} is unreadable"
    if rec["value"] is None:
        return f"{name} is nil"
    return None


def cross_checks(pages: List[Dict], rounding: str = "unstated") -> List[Dict]:
    """D21 item 4, Q23. The pieces may sit on different pages.
    (a) total assets = total liabilities and net assets, exactly: it is the same amount printed twice, so it rounds
        or is cut to the same integer. (b) total liabilities and net assets = total liabilities + total net assets,
        with the bound for two items. A missing piece skips the check and the reason names it."""
    periods = []
    for page in pages:
        for period in page["periods"]:
            if period not in periods:
                periods.append(period)
    checks: List[Dict] = []
    for period in periods:
        assets, lna = _find(pages, "assets", period), _find(pages, "liabilities_net_assets", period)
        reason = _usable(assets, "total assets") or _usable(lna, "total liabilities and net assets")
        if reason:
            checks.append(_skipped(A_LABEL, period, reason, _ref(assets) + _ref(lna)))
        else:
            diff = lna["value"] - assets["value"]
            checks.append({"label": f"{assets['label']} = {lna['label']}", "period": period, "expected": assets["value"],
                           "printed": lna["value"], "difference": diff, "bound": 0, "items": 1,
                           "status": "pass" if diff == 0 else "failed", "reason": "",
                           "rows": _ref(assets) + _ref(lna)})
        liabilities, net_assets = _find(pages, "liabilities", period), _find(pages, "net_assets", period)
        reasons = [r for r in (_usable(lna, "total liabilities and net assets"), _usable(liabilities, "total liabilities"),
                               _usable(net_assets, "total net assets")) if r]
        if reasons:
            checks.append(_skipped(B_LABEL, period, "; ".join(reasons), _ref(lna) + _ref(liabilities) + _ref(net_assets)))
        else:
            expected = liabilities["value"] + net_assets["value"]
            diff = lna["value"] - expected
            bound = bound_for(2, rounding)
            checks.append({"label": f"{lna['label']} = {liabilities['label']} + {net_assets['label']}", "period": period,
                           "expected": expected, "printed": lna["value"], "difference": diff, "bound": bound, "items": 2,
                           "status": "failed" if abs(diff) > bound else "pass", "reason": "",
                           "rows": _ref(lna) + _ref(liabilities) + _ref(net_assets)})
    return checks
