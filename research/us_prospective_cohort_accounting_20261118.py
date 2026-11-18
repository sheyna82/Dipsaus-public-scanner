"""Offline non-cherry-picked prospective cohort accounting.

All enrolled records remain in denominator, including missing forward bars.
Only aggregate counts are returned; no symbols, prices or timestamps exposed.
"""
from research.us_strict_forward_evidence_20261118 import evaluate_strict_forward

COHORTS = ("EVALUATED", "OVERFLOW", "PENDING", "REJECTED")

def audit_prospective_cohort(enrollments):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(enrollments, list):
        return {**base, "blocks": ["ENROLLMENTS_INVALID"]}
    seen = set()
    by_cohort = {name: {"enrolled": 0, "forward_evaluated": 0,
                        "no_forward_evidence": 0, "blocked": 0,
                        "breakout_observed": 0, "retest_reclaim_observed": 0}
                 for name in COHORTS}
    for item in enrollments:
        if not isinstance(item, dict):
            return {**base, "blocks": ["ENROLLMENT_INVALID"]}
        symbol, cohort = item.get("symbol"), item.get("cohort")
        if (not isinstance(symbol, str) or not symbol.strip() or symbol in seen
                or cohort not in COHORTS):
            return {**base, "blocks": ["IDENTITY_COHORT_OR_DUPLICATE_INVALID"]}
        seen.add(symbol)
        row = by_cohort[cohort]
        row["enrolled"] += 1
        result = evaluate_strict_forward(item.get("snapshot"), item.get("completed_bars"))
        status = result["status"]
        if status == "STRICT_FORWARD_RESEARCH_ONLY":
            row["forward_evaluated"] += 1
            if result["pattern_status"] in ("BREAKOUT_OBSERVED", "RETEST_OBSERVED", "RESEARCH_REVIEW"):
                row["breakout_observed"] += 1
            if result["pattern_status"] == "RESEARCH_REVIEW":
                row["retest_reclaim_observed"] += 1
        elif status == "NO_FORWARD_EVIDENCE":
            row["no_forward_evidence"] += 1
        else:
            row["blocked"] += 1
    return {**base, "status": "COHORT_ACCOUNTED_RESEARCH_ONLY",
            "total_enrolled": len(enrollments), "by_cohort": by_cohort,
            "verified_profitable_missed_trades": None,
            "limitations": ["No sample selection from observed outcomes",
                            "No profit-rate estimate; missing and blocked remain denominator",
                            "No fixed horizon or independently verified provider evidence"]}
