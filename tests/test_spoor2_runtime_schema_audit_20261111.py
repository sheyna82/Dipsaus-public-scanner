"""Regression for structural schema audit; source snapshots are never trade evidence."""
import unittest
from research.spoor2_runtime_schema_audit_20261111 import inspect_report


class SchemaAuditTests(unittest.TestCase):
    def test_us_complete_and_bad_pivot(self):
        valid = {"symbol": "TEST", "last_close_usd": 52,
                 "recovery_map": {
                     "recent_10d_low_invalidation_reference_usd": 49,
                     "historical_overhead_pivot_zones": [{"low_usd": 55}]}}
        bad = {"symbol": "BAD", "last_close_usd": 51,
               "recovery_map": {
                   "recent_10d_low_invalidation_reference_usd": 49,
                   "historical_overhead_pivot_zones": [{"low_usd": float("nan")}]}}
        result = inspect_report({"candidates": [valid, bad]}, "US")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["blocked"], 1)
        self.assertIn("US_PIVOT_INVALID", result["issues"])
        self.assertFalse(result["trade_ready"])

    def test_eu_pence_and_missing_resistance(self):
        valid = {"symbol": "RIO.L", "historical_close": 6450, "currency": "GBp",
                 "historical_first_friction": {"price": 6460},
                 "historical_meaningful_resistance": {"price": 7227}}
        bad = dict(valid, currency="UNKNOWN", historical_meaningful_resistance=None)
        result = inspect_report({"candidates": [valid, bad]}, "EU")
        self.assertEqual(result["blocked"], 1)
        self.assertIn("EU_CURRENCY_UNRECOGNIZED", result["issues"])
        self.assertIn("EU_HISTORICAL_MEANINGFUL_RESISTANCE_INVALID", result["issues"])

    def test_unknown_and_invalid_input(self):
        self.assertEqual(inspect_report({}, "US")["status"], "INVALID_REPORT")
        self.assertEqual(inspect_report({"candidates": []}, "OTHER")["status"], "INVALID_REPORT")
        self.assertEqual(inspect_report({"candidates": [None]}, "US")["blocked"], 1)


if __name__ == "__main__":
    unittest.main()
