"""Offline tests for event quote gap diagnostics."""
import unittest
from datetime import datetime, timezone
from event_quote_gap_diagnostics import diagnose_event_quote_row

class GapDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 15, tzinfo=timezone.utc)
        self.row = dict(symbol="PLTR", provider_symbol="PLTR",
                        provider_currency="USD", provider_quote=100,
                        provider_quote_utc="2026-11-02T14:59:00+00:00",
                        provider_freshness_pass=True, provider_source="Yahoo Finance 1m",
                        market_session_verified=True, provider_delayed=False)

    def test_existing_watch_shape_reports_missing_evidence(self):
        row = dict(symbol="PLTR", provider_quote=100,
                   provider_quote_utc="2026-11-02T14:59:00+00:00",
                   provider_freshness_pass=True)
        result = diagnose_event_quote_row(row, "PLTR", self.now)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("market_session_verified", result["missing_fields"])
        self.assertIn("provider_delayed", result["missing_fields"])
        self.assertFalse(result["execution_ready"])

    def test_valid_research_quote_never_enables_execution(self):
        result = diagnose_event_quote_row(self.row, "PLTR", self.now)
        self.assertEqual(result["status"], "VALIDATED_RESEARCH_QUOTE")
        self.assertEqual(result["missing_fields"], [])
        self.assertFalse(result["execution_ready"])

    def test_wrong_identity_and_stale_quote_block(self):
        row = dict(self.row, provider_symbol="AMD")
        result = diagnose_event_quote_row(row, "PLTR", self.now)
        self.assertIn("provider_symbol", result["invalid_fields"])
        self.assertEqual(result["status"], "BLOCKED")
        row = dict(self.row, provider_quote_utc="2026-11-02T14:50:00+00:00")
        self.assertEqual(diagnose_event_quote_row(row, "PLTR", self.now)["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
