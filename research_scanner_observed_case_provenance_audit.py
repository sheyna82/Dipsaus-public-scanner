"""Audit dated screenshot observations without promoting clock times to UTC.

The eight cases are evidence of observed notifications, not verified scanner
decisions, provider acknowledgments, fills or trade outcomes.
"""
from research_notification_signal_cases import CASES_2026_10_26
from research_scanner_signal_chain_provenance_gate import audit_signal_chain


def audit_observed_cases(cases=CASES_2026_10_26, *, observation_day="2026-10-26"):
    rows = []
    for index, case in enumerate(cases):
        # Do not infer timezone, UTC instant, rule version or a trade from a
        # screenshot's displayed local clock time.
        rows.append({
            "signal_id": f"observed-{observation_day}-{index:02d}",
            "symbol": case.symbol,
            "family": case.family,
            "observed_clock_time_unverified": case.observed_local_time,
            "decision_utc": None,
            "generated_utc": None,
            "provider_accepted_utc": None,
            "entry_utc": None,
            "decision_source_verified": False,
            "signal_rule_version_verified": False,
            "point_in_time_inputs_verified": False,
            "market_data_source_verified": False,
            "execution_verified": False,
            "costs_and_currency_verified": False,
            "phone_receipt_verified": False,
        })
    result = audit_signal_chain(rows)
    result["observation_count"] = len(cases)
    result["observation_source"] = "dated_notification_case_examples"
    result["observation_day"] = observation_day
    result["limitations"] = [
        "Displayed local clock times have no verified timezone or UTC instant",
        "Screenshots do not independently attest scanner decision timestamps",
        "No verified executable fills or costs",
        "Provider acceptance and device receipt are not independently proven",
    ]
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(audit_observed_cases(), indent=2))
