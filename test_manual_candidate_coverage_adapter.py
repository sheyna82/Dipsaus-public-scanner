import unittest
from datetime import datetime, timezone
from manual_candidate_coverage_adapter import (
    from_manual_configs, from_manual_report, audit_manual_candidate_coverage)
from private_candidate_registry import public_aggregate

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)
TS = NOW.isoformat()

class ManualAdapterTests(unittest.TestCase):
    def test_merges_supplemental_with_stable_id(self):
        r = from_manual_configs({"candidates": {"NU": {"monitor_mode": "research_only"}}},
                                {"candidates": {"NU": {"currency": "USD"},
                                                "STNE": {"currency": "USD"}}})
        self.assertEqual([x["id"] for x in r["candidates"]],
                         ["manual:NU", "manual:STNE"])
        self.assertEqual(r["candidates"][0]["currency"], "USD")

    def test_watch_counts_as_checked_not_buy(self):
        r = from_manual_report({"rows": [{"symbol": "NU", "status": "WATCH",
                                         "provider_freshness_pass": True}]}, checked_at=TS)
        self.assertEqual(r[0]["status"], "FRESH_CHECKED")

    def test_stale_report_is_blocked(self):
        r = from_manual_report({"rows": [{"symbol": "NU", "status": "WATCH",
                                         "provider_freshness_pass": False}]}, checked_at=TS)
        self.assertEqual(r[0]["status"], "DATA_BLOCKED")

    def test_missing_candidate_is_overdue(self):
        r = audit_manual_candidate_coverage(
            {"candidates": {"NU": {}, "STNE": {}}}, {},
            {"rows": [{"symbol": "NU", "status": "WATCH",
                       "provider_freshness_pass": True}]}, checked_at=TS, now=NOW)
        self.assertEqual(r["summary"]["overdue"], 1)
        self.assertFalse(r["summary"]["reconciled"])
        self.assertNotIn("NU", str(public_aggregate(r)))

    def test_excludes_portfolio_and_auto_rows(self):
        r = from_manual_report({"rows": [
            {"symbol": "NU", "watch_type": "AUTO-US-DISCOVERY"},
            {"symbol": "EXE", "watch_type": "PORTFOLIO-REENTRY"}]}, checked_at=TS)
        self.assertEqual(r, [])

    def test_duplicate_manual_rows_fail_closed(self):
        with self.assertRaises(ValueError):
            from_manual_report({"rows": [
                {"symbol": "NU"}, {"symbol": "NU"}]}, checked_at=TS)

    def test_no_config_no_implicit_candidate(self):
        r = from_manual_configs({"candidates": {}}, {})
        self.assertEqual(r["candidates"], [])

if __name__ == "__main__":
    unittest.main()
