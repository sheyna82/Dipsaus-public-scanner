"""Regression tests for event outcome arithmetic; no real market data."""
import unittest
from research_event_snapshot_gate import audit_event_snapshot
from research_event_outcome_score import calculate_event_outcomes


def fixture():
    snap = audit_event_snapshot(
        "AMD", "2026-10-24T12:00:00Z", "2026-11-03",
        "100", "200", "synthetic_fixture", "2026-10-24")
    dates = ["2026-11-04", "2026-11-05", "2026-11-06",
             "2026-11-09", "2026-11-10"]
    stocks = [{"date": d, "close": str(100 + i)} for i, d in enumerate(dates, 1)]
    benchmarks = [{"date": d, "close": "200"} for d in dates]
    return snap, stocks, benchmarks


class EventOutcomeTests(unittest.TestCase):
    def test_returns_at_one_three_five_sessions(self):
        result = calculate_event_outcomes(*fixture())
        self.assertEqual(set(result["horizons"]), {1, 3, 5})
        self.assertEqual(result["horizons"][3]["excess_return"], "0.03")
        self.assertFalse(result["predictive_skill_established"])
        self.assertFalse(result["trade_ready"])

    def test_missing_session_or_mismatched_dates_rejected(self):
        snap, stocks, benchmarks = fixture()
        with self.assertRaisesRegex(ValueError, "outcome_session_length_mismatch"):
            calculate_event_outcomes(snap, stocks, benchmarks[:-1])
        benchmarks[2]["date"] = "2026-11-07"
        with self.assertRaisesRegex(ValueError, "outcome_session_date_mismatch"):
            calculate_event_outcomes(snap, stocks, benchmarks)

    def test_pre_event_outcome_rejected(self):
        snap, stocks, benchmarks = fixture()
        stocks[0]["date"] = benchmarks[0]["date"] = "2026-11-03"
        with self.assertRaisesRegex(ValueError, "outcome_sessions_not_ordered_after_event"):
            calculate_event_outcomes(snap, stocks, benchmarks)

    def test_invalid_outcome_price_rejected(self):
        snap, stocks, benchmarks = fixture()
        stocks[1]["close"] = "NaN"
        with self.assertRaisesRegex(ValueError, "invalid_outcome_close"):
            calculate_event_outcomes(snap, stocks, benchmarks)


if __name__ == "__main__":
    unittest.main()
