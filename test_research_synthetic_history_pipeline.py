"""Synthetic-only end-to-end historical research rehearsal.

No external feeds, private state, ticker symbols, real orders or persistence.
"""
import unittest

from research_historical_event_contract import validate_historical_events
from research_historical_coverage import audit_historical_coverage
from research_walk_forward_validation import evaluate_walk_forward

CUTOFF = "2026-02-01T00:00:00Z"
DIGEST = "a" * 64
FEATURE = {
    "net_profit_eur": 200, "net_rr": 3, "relative_volume": 1.5,
    "market_context": .8, "sector_context": .8,
    "risk_inputs": {
        "bid": 99.9, "ask": 100, "average_daily_turnover_eur": 2000000,
        "relative_volume": 1.5, "earnings_calendar_checked": True,
        "sessions_until_earnings": 9,
    },
}

def fixture():
    specs = [
        # candidate, decision, observation, outcome, return
        ("1", "SELECTED", "2026-01-02T00:00:00Z", "2026-01-12T00:00:00Z", 5),
        ("2", "REJECTED", "2026-01-03T00:00:00Z", "2026-01-13T00:00:00Z", -6),
        ("3", "DEFERRED", "2026-02-02T00:00:00Z", "2026-02-12T00:00:00Z", -2),
        ("4", "SELECTED", "2026-02-03T00:00:00Z", None, None),
    ]
    events, signals, outcomes, complete = [], [], [], []
    for idx, (suffix, decision, start, end, value) in enumerate(specs, 1):
        cid = format(idx, "032x")
        signals.append({"id": cid, "decision": decision, "observed_utc": start})
        events.append({"schema_version": 1, "event_id": format(idx, "032x"),
                       "candidate_id": cid, "observed_utc": start,
                       "event_type": "SIGNAL", "source_digest": DIGEST,
                       "feature_digest": DIGEST, "decision": decision})
        if end is not None:
            outcomes.append({"id": cid, "observed_utc": end, "return_pct": value})
            events.append({"schema_version": 1, "event_id": format(idx + 100, "032x"),
                           "candidate_id": cid, "observed_utc": end,
                           "event_type": "OUTCOME", "source_digest": DIGEST,
                           "return_pct": value, "horizon_sessions": 5})
            features = {**FEATURE, "id": cid,
                        "risk_inputs": dict(FEATURE["risk_inputs"])}
            if decision == "REJECTED":
                features["net_profit_eur"] = 149
            if decision == "DEFERRED":
                features["risk_inputs"]["sessions_until_earnings"] = 2
            complete.append({"id": cid, "features": features,
                             "features_observed_utc": start,
                             "outcome_observed_utc": end,
                             "outcome_return_pct": value})
    return events, signals, outcomes, complete

class SyntheticHistoricalPipelineTests(unittest.TestCase):
    def test_full_synthetic_pipeline_retains_rejections_and_missing_outcomes(self):
        events, signals, outcomes, complete = fixture()
        contract = validate_historical_events(events)
        coverage = audit_historical_coverage(signals, outcomes)
        walk = evaluate_walk_forward(complete, cutoff_utc=CUTOFF)
        self.assertEqual(contract["status"], "HISTORICAL_EVENT_CONTRACT_RESEARCH_ONLY")
        self.assertEqual(contract["signal_count"], 4)
        self.assertEqual(contract["missing_outcome_count"], 1)
        self.assertEqual(coverage["decision_counts"],
                         {"SELECTED": 2, "REJECTED": 1, "DEFERRED": 1})
        self.assertEqual(coverage["outcome_coverage_fraction"], .75)
        self.assertEqual(walk["train"]["observations"], 2)
        self.assertEqual(walk["test"]["observations"], 1)
        self.assertEqual(walk["train"]["all_candidate_mean_return_pct"], -.5)
        self.assertEqual(walk["train"]["mean_observed_return_pct"], 5)
        self.assertEqual(walk["train"]["not_selected_mean_return_pct"], -6)
        self.assertEqual(walk["test"]["research_review_candidates"], 0)
        self.assertFalse(contract["archive_completeness_verified"])
        self.assertFalse(coverage["complete_candidate_universe_verified"])
        self.assertFalse(walk["trade_ready"])
        self.assertFalse(walk["order_placement_enabled"])

    def test_outcome_missing_cannot_be_silently_counted_as_complete(self):
        events, signals, outcomes, complete = fixture()
        del outcomes[0]["return_pct"]
        self.assertEqual(audit_historical_coverage(signals, outcomes)["reason"],
                         "INVALID_OUTCOME_VALUE")
        self.assertEqual(validate_historical_events(events)["outcome_count"], 3)

    def test_unknown_field_cannot_be_added_to_archived_event(self):
        events, _, _, _ = fixture()
        events[0]["symbol"] = "synthetic-ticker"
        self.assertEqual(validate_historical_events(events)["reason"],
                         "UNKNOWN_TYPE_OR_FIELDS")

if __name__ == "__main__":
    unittest.main()
