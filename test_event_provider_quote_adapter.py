"""Offline fail-closed tests for provider-to-event quote adapter."""
import unittest
from datetime import datetime, timezone
from event_provider_quote_adapter import provider_event_quote_metrics

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc)
        self.row = dict(symbol="PLTR", provider_symbol="PLTR", provider_currency="USD",
                        provider_quote=100.5, provider_quote_utc="2026-11-02T14:59:00+00:00",
                        provider_freshness_pass=True, market_session_verified=True,
                        provider_delayed=False, provider_source="Yahoo Finance 1m")

    def test_valid_observation(self):
        result = provider_event_quote_metrics(self.row, "PLTR", self.now)
        self.assertEqual(result["fresh_quote"]["price"], 100.5)

    def test_missing_or_unsafe_fields_block(self):
        for key, value in [("provider_symbol","AMD"), ("provider_currency","EUR"),
                           ("provider_quote_utc",None), ("provider_quote_utc","2026-11-02T14:50:00+00:00"),
                           ("provider_quote",None), ("provider_source",None),
                           ("provider_freshness_pass",False), ("market_session_verified",False),
                           ("provider_delayed",True)]:
            with self.subTest(key=key):
                row = dict(self.row, **{key:value})
                self.assertEqual(provider_event_quote_metrics(row,"PLTR",self.now),{})

    def test_missing_identity_and_source_block(self):
        for key in ("symbol", "provider_symbol", "provider_source", "market_session_verified", "provider_delayed"):
            row = dict(self.row)
            row.pop(key)
            if key == "symbol":
                row.pop("provider_symbol")
            self.assertEqual(provider_event_quote_metrics(row,"PLTR",self.now),{})

if __name__ == "__main__":
    unittest.main()
