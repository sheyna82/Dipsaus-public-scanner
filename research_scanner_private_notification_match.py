"""Research-only, in-memory private notification evidence matching.

No raw private state is returned or written. Matching by ticker alone is never
sufficient to identify one screenshot observation; ambiguity fails closed.
"""
from datetime import date, datetime, timedelta, timezone
from research_notification_signal_cases import CASES_2026_10_26
from research_notification_timestamp_extract import verified_notification_times


def match_observed_notifications(state, cases=CASES_2026_10_26, *,
                                 observation_day="2026-10-26"):
    day = date.fromisoformat(observation_day)
    symbols = sorted({c.symbol for c in cases})
    notifications = verified_notification_times(state, symbols)
    by_symbol = {symbol: [] for symbol in symbols}
    for record in notifications:
        stamp = datetime.fromisoformat(record["notification_utc"])
        # A screenshot has no attested timezone. Include neighboring UTC dates
        # for candidate discovery; do not turn this into a verified match.
        if abs((stamp.astimezone(timezone.utc).date() - day).days) <= 1:
            by_symbol[record["symbol"]].append(record)
    results = []
    for index, case in enumerate(cases):
        matches = by_symbol[case.symbol]
        exact_family_candidates = sum(
            record["key_family"] == case.family for record in matches
        )
        if len(matches) == 1:
            status = "unique_symbol_adjacent_utc_days_candidate_unverified_link"
        elif len(matches) == 0:
            status = "no_candidate_within_adjacent_utc_days"
        else:
            status = "ambiguous_multiple_adjacent_utc_days_records"
        # UTC calendar day can differ from the screenshot's local day.
        # Never assign a matched notification to a screenshot or a trade.
        results.append({
            "case_index": index,
            "symbol": case.symbol,
            "family": case.family,
            "candidate_private_record_count": len(matches),
            "exact_family_candidate_count": exact_family_candidates,
            "match_status": status,
            "screenshot_link_verified": False,
            "scanner_decision_verified": False,
            "phone_delivery_verified": False,
            "execution_verified": False,
        })
    return {
        "research_only": True,
        "trade_ready": False,
        "private_state_exported": False,
        "observation_count": len(results),
        "cases": results,
        "warnings": [
            "Adjacent UTC date matching is only a candidate lookup, not screenshot identity proof",
            "Exact family matching is descriptive and does not verify scanner origin",
            "Private timestamps, key families and delivery statuses are not exported",
            "No historical profit or execution claim is supported",
        ],
    }
