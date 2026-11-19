"""Historical dossier integration: synthetic fixtures, no provider secrets."""
import unittest
from research.spoor2_historical_report_bridge_20261111 import analyze_candidate, analyze_report


class HistoricalBridgeTests(unittest.TestCase):
    def test_economic_levels_not_trade_signal(self):
        candidate = {
            "symbol": "EQT", "last_close_usd": 52.05, "trade_ready": True,
            "recovery_map": {
                "recent_10d_low_invalidation_reference_usd": 49,
                "historical_overhead_pivot_zones": [
                    {"low_usd": 54.25}, {"low_usd": 57.30}, {"low_usd": 51.20}],
            },
        }
        result = analyze_candidate(candidate)
        self.assertEqual(result["levels"]["required_2r_target_usd"], 58.15)
        self.assertEqual(result["levels"]["resistance_references_usd"], [54.25, 57.3])
        self.assertEqual(result["notification_channel"], "RESEARCH")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["order_placement_enabled"])
        self.assertIn("GEEN KOOP", result["notification_subject"])

    def test_no_price_never_fabricates_levels(self):
        result = analyze_candidate({"symbol": "INGM", "recovery_map": {}})
        self.assertEqual(result["levels"]["status"], "UNKNOWN")
        self.assertFalse(result["trade_ready"])

    def test_invalid_report_fails_closed(self):
        self.assertEqual(analyze_report({})["status"], "UNKNOWN")
        self.assertEqual(analyze_candidate(None)["notification_channel"], "NONE")

    def test_multiple_historical_rows_all_research(self):
        report = {"candidates": [
            {"symbol": "BTE", "last_close_usd": 4.15, "recovery_map": {}},
            {"symbol": "CXW", "last_close_usd": 31.45, "recovery_map": {}},
        ]}
        result = analyze_report(report)
        self.assertEqual(len(result["rows"]), 2)
        self.assertTrue(all(row["notification_channel"] == "RESEARCH"
                            and not row["trade_ready"] for row in result["rows"]))


if __name__ == "__main__":
    unittest.main()
