"""Research-only eligibility classification of dated scanner observations.

Observations cannot be promoted to historical trades without independent,
point-in-time evidence. Exit reviews are not entry signals.
"""
from collections import Counter
from research_notification_signal_cases import CASES_2026_10_26

ENTRY_RESEARCH_FAMILIES = frozenset({
    "EARLY_RECOVERY", "BREAKOUT_HOLD_RETEST", "EU_ENTRY_RESEARCH",
})
EXIT_REVIEW_FAMILIES = frozenset({"EXIT_ZONE_REVIEW"})


def classify_observed_cohort(cases=CASES_2026_10_26):
    rows = []
    for case in cases:
        if case.family in EXIT_REVIEW_FAMILIES:
            role = "existing_position_exit_review"
        elif case.family in ENTRY_RESEARCH_FAMILIES:
            role = "candidate_entry_research"
        else:
            role = "unknown_family_excluded"
        rows.append({
            "symbol": case.symbol,
            "family": case.family,
            "role": role,
            "verified_trade": False,
            "return_study_eligible": False,
        })
    counts = Counter(row["role"] for row in rows)
    return {
        "research_only": True,
        "trade_ready": False,
        "observations": len(rows),
        "role_counts": dict(sorted(counts.items())),
        "verified_trades": 0,
        "return_study_eligible": 0,
        "rows": rows,
        "limitations": [
            "Screenshot observations lack independently verified decision and execution evidence",
            "Exit-review signals must not enter the entry-return denominator",
            "Entry research alerts are candidates, not broker fills",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(classify_observed_cohort(), indent=2))
