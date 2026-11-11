"""Offline recovery score outcome report; never interpret as calibrated probabilities."""
import math

STATUSES = frozenset(("GAIN_FIRST", "LOSS_FIRST", "TIMEOUT",
                      "AMBIGUOUS_SAME_BAR", "INSUFFICIENT_FUTURE_DATA"))
BANDS = {"high": (5, 7), "medium": (3, 4), "low": (0, 2)}


def summarize_recovery_scores(records, minimum_resolved=20):
    if not isinstance(records, (list, tuple)) or type(minimum_resolved) is not int or minimum_resolved < 1:
        return None
    ids = set()
    groups = {band: [] for band in BANDS}
    for record in records:
        if not isinstance(record, dict):
            return None
        ident, score, status = (record.get(k) for k in ("id", "score", "status"))
        if (type(ident) is not str or not ident or ident in ids or
                type(score) is not int or not 0 <= score <= 7 or status not in STATUSES):
            return None
        ids.add(ident)
        band = next(k for k, (lo, hi) in BANDS.items() if lo <= score <= hi)
        groups[band].append(status)
    report = {}
    for band, statuses in groups.items():
        counts = {status: statuses.count(status) for status in sorted(STATUSES)}
        resolved = counts["GAIN_FIRST"] + counts["LOSS_FIRST"] + counts["TIMEOUT"]
        report[band] = {"nominated": len(statuses), "resolved": resolved,
                        "counts": counts, "coverage_pct": round(100 * resolved / len(statuses), 2) if statuses else None,
                        "gain_first_rate_pct": round(100 * counts["GAIN_FIRST"] / resolved, 2)
                        if resolved >= minimum_resolved else None,
                        "minimum_resolved_met": resolved >= minimum_resolved}
    return {"bands": report, "minimum_resolved": minimum_resolved,
            "research_only": True, "trade_ready": False, "order_instruction": None,
            "probabilities_calibrated": False,
            "limitations": "Descriptive in-sample grouping only; unresolved cases included in coverage; no causality, costs, independent data or walk-forward validation."}
