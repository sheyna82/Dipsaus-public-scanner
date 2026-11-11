"""Offline contract fixtures based on inspected US/EU migration report shapes."""
import unittest
from research.spoor2_runtime_schema_adapters_20261111 import adapt_runtime_report


class RuntimeAdapterTests(unittest.TestCase):
    def test_us_recovery_map_schema(self):
        report = {"candidates": [{
            "symbol": "TESTUS", "last_bar_date": "2026-11-10",
            "last_close_usd": 52.05,
            "recovery_map": {
                "status": "STRUCTURED_HISTORICAL_RESEARCH_ONLY",
                "historical_overhead_pivot_zones": [
                    {"low_usd": 55.5, "high_usd": 56, "touches": 3,
                     "status": "HISTORICAL_PIVOT_CLUSTER_UNCONFIRMED"}],
                "recent_10d_low_invalidation_reference_usd": 49,
                "invalidation_confirmed": False, "resistance_confirmed": False,
                "trade_ready": False,
            },
        }]}
        result = adapt_runtime_report(report, "US")
        row = result["rows"][0]
        self.assertEqual(row["levels"]["invalidation_reference_usd"], 49)
        self.assertEqual(row["levels"]["resistance_references_usd"], [55.5])
        self.assertEqual(row["source_bar_date"], "2026-11-10")
        self.assertFalse(row["trade_ready"])

    def test_eu_report_not_misinterpreted_as_usd_quote(self):
        report = {"candidates": [{
            "symbol": "TESTEU", "currency": "EUR",
            "historical_close": 52.05,
            "historical_first_friction": 54.5,
            "historical_meaningful_resistance": 60,
            "provider_bid": 52.01, "provider_ask": 52.09,
            "provider_freshness_pass": True, "broker_verify_now": True,
            "trade_ready": True,
        }]}
        row = adapt_runtime_report(report, "EU")["rows"][0]
        self.assertEqual(row["notification_channel"], "RESEARCH")
        self.assertFalse(row["trade_ready"])
        self.assertEqual(row["historical_first_friction"], 54.5)
        self.assertNotIn("broker_quote_verified", row)
        self.assertIn("EU_EXECUTABLE_BROKER_EVIDENCE_NOT_CONNECTED", row["blocks"])

    def test_unknown_market_and_malformed_report(self):
        self.assertEqual(adapt_runtime_report({}, "US")["status"], "UNKNOWN")
        self.assertEqual(adapt_runtime_report({"candidates": []}, "OTHER")["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
