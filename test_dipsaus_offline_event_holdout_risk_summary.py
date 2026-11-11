import unittest
from dipsaus_offline_event_holdout_risk_summary import summarize_holdouts


def record(symbol, count, adverse, positive, mean):
    return {"symbol": symbol, "chronological_holdout": {
        "status": "DESCRIPTIVE_CHRONOLOGICAL_SPLIT",
        "test": {"count": count, "severe_intraperiod_drawdown_count": adverse,
                 "positive_count": positive, "mean_net_pct": mean}}}


class HoldoutRiskSummaryTests(unittest.TestCase):
    def test_weighted_rate_and_mean(self):
        out = summarize_holdouts([record("A", 2, 1, 1, 2), record("B", 3, 2, 2, -1)])
        self.assertEqual(out["status"], "DESCRIPTIVE_RISK_AGGREGATE")
        self.assertEqual(out["event_count"], 5)
        self.assertEqual(out["severe_intraperiod_drawdown_event_rate_pct"], 60)
        self.assertEqual(out["event_weighted_mean_net_pct"], 0.2)
        self.assertFalse(out["predictive_edge_proven"])

    def test_inconsistent_counts_block(self):
        self.assertEqual(summarize_holdouts([record("A", 1, 2, 0, 1)])["status"],
                         "DATA_BLOCKED")

    def test_missing_holdout_blocks(self):
        self.assertEqual(summarize_holdouts([{"symbol": "A"}])["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
