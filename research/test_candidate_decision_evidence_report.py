import unittest
from candidate_decision_evidence_report import build

class EvidenceReportTests(unittest.TestCase):
    def test_descriptive_metrics_never_become_forecasts(self):
        src = {"candidates": [{"symbol": "TEST", "patterns": {
            "recovery": {"cohorts": {"volume_ratio_20d": {
                "n": 40, "median_excess_pct": 1.2, "median_mae_pct": -5}}}}}]}
        row = build(src)["candidates"][0]
        self.assertEqual(row["descriptive_median_excess_pct"], 1.2)
        self.assertIsNone(row["estimates"]["expected_net_return_pct"])
        self.assertIsNone(row["estimates"]["validated_win_probability"])
        self.assertEqual(row["status"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(row["trade_ready"])
        self.assertFalse(row["automatic_orders"])

    def test_invalid_source_rejected(self):
        with self.assertRaises(ValueError):
            build({"candidates": None})

    def test_blocked_symbols_do_not_create_fake_records(self):
        result = build({"candidates": [{"symbol": "TEST", "status": "DATA_BLOCKED"}]})
        self.assertEqual(result["candidates"], [])

if __name__ == "__main__":
    unittest.main()
