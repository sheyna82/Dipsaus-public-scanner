"""End-to-end synthetic private-hydration -> report -> coverage test.

No actual Secrets, provider calls, state writes or notifications.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone
from private_runtime import hydrate
from manual_candidate_coverage_adapter import audit_manual_candidate_coverage
from private_candidate_registry import public_aggregate

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)

class SyntheticPrivateIntegrationTests(unittest.TestCase):
    def test_hydrated_candidate_missing_from_scan_is_overdue(self):
        bundle = {
            "manual_recovery_triggers.json": {
                "candidates": {"SYNTHETIC_A": {"monitor_mode": "research_only"},
                               "SYNTHETIC_B": {"currency": "USD"}}},
            "manual_recovery_triggers_supplemental.json": {
                "candidates": {"SYNTHETIC_C": {"currency": "USD"}}},
            "portfolio_reentry_watch.json": {"candidates": {}},
            "profit_exit_watch.json": {"candidates": {}},
            "notification_quality_gate.json": {},
        }
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            cwd = os.getcwd()
            try:
                os.chdir(temp)
                hydrate(json.dumps(bundle))
                primary = json.loads(Path("config/manual_recovery_triggers.json").read_text())
                extra = json.loads(Path("config/manual_recovery_triggers_supplemental.json").read_text())
                report = {"generated_utc": NOW.isoformat(), "rows": [
                    {"symbol": "SYNTHETIC_A", "status": "WATCH",
                     "provider_freshness_pass": True},
                    {"symbol": "SYNTHETIC_B", "status": "DATA-BLOCKED",
                     "provider_freshness_pass": False},
                ]}
                result = audit_manual_candidate_coverage(
                    primary, extra, report, checked_at=NOW.isoformat(), now=NOW)
            finally:
                os.chdir(cwd)
        self.assertEqual(result["summary"]["active"], 3)
        self.assertEqual(result["summary"]["fresh_checked"], 1)
        self.assertEqual(result["summary"]["blocked"], 1)
        self.assertEqual(result["summary"]["overdue"], 1)
        self.assertFalse(result["summary"]["reconciled"])
        self.assertNotIn("SYNTHETIC_A", str(public_aggregate(result)))

if __name__ == "__main__":
    unittest.main()
