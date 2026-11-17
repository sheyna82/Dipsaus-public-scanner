"""No offline evidence combination may enable an actionable trade."""
import unittest
from research.us_shadow_decision_20261117 import assess_shadow_with_market_evidence

class ShadowDecisionTests(unittest.TestCase):
    def test_no_inputs_fail_closed(self):
        r = assess_shadow_with_market_evidence(None, None)
        self.assertIn("CANDIDATE_INPUT_MISSING", r["blocks"])
        self.assertIn("MARKET_EVIDENCE_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])
        self.assertFalse(r["automatic_orders"])
    def test_empty_candidate_and_market_fail_closed(self):
        r = assess_shadow_with_market_evidence({}, {})
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertIn("MARKET_EVIDENCE_INVALID", r["blocks"])
        self.assertIn("CANDIDATE_NOT_CONFIRMED", r["blocks"])
    def test_independence_and_license_never_auto_granted(self):
        r = assess_shadow_with_market_evidence({}, None)
        self.assertIn("SOURCE_INDEPENDENCE_UNVERIFIED", r["blocks"])
        self.assertIn("DATA_LICENSE_UNVERIFIED", r["blocks"])
        self.assertIn("EXCHANGE_CALENDAR_UNVERIFIED", r["blocks"])
    def test_invalid_candidate_quote_type_fails_closed(self):
        r = assess_shadow_with_market_evidence({"quote": ["malformed"]}, None)
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertIn("CANDIDATE_quote_VALUE", r["blocks"])
        self.assertFalse(r["notify"])

    def test_invalid_candidate_timeframes_type_fails_closed(self):
        r = assess_shadow_with_market_evidence({"timeframes": 42}, None)
        self.assertEqual(r["status"], "SHADOW_BLOCKED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["automatic_orders"])

    def test_symbol_mismatch_blocks_join(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "MSFT"})
        self.assertIn("INSTRUMENT_JOIN_SYMBOL_MISMATCH", r["blocks"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["notify"])

    def test_missing_candidate_symbol_blocks_join(self):
        r = assess_shadow_with_market_evidence({}, {"ticker": "AAPL"})
        self.assertIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])

    def test_missing_market_symbol_blocks_join(self):
        r = assess_shadow_with_market_evidence({"symbol": "AAPL"}, {})
        self.assertIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])

    def test_case_insensitive_symbol_join(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": " aapl "}, {"ticker": "AAPL"})
        self.assertNotIn("INSTRUMENT_JOIN_SYMBOL_MISMATCH", r["blocks"])
        self.assertNotIn("INSTRUMENT_JOIN_IDENTITY_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_missing_source_metadata_blocks(self):
        r = assess_shadow_with_market_evidence({}, {})
        self.assertIn("SOURCE_RECORD_MISSING", r["blocks"])
        self.assertIn("SOURCE_METADATA_INCOMPLETE", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_source_mic_mismatch_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            source_identity={"mic": "XNYS"})
        self.assertIn("SOURCE_MARKET_MIC_MISMATCH", r["blocks"])
        self.assertFalse(r["notify"])

    def test_complete_synthetic_metadata_not_trusted(self):
        source = {"provider_id": "synthetic", "dataset_id": "bars",
                  "instrument_id": "AAPL", "mic": "XNAS",
                  "retrieval_url": "https://example.org/data",
                  "retrieval_reference": "offline", "license_reference": "offline",
                  "content_sha256": "a" * 64}
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            source_identity=source)
        self.assertEqual(r["source_identity"]["status"], "METADATA_COMPLETE_UNVERIFIED")
        self.assertIn("SOURCE_INDEPENDENCE_UNVERIFIED", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_missing_calendar_evidence_blocks(self):
        r = assess_shadow_with_market_evidence({}, {}, session_date="2026-11-17")
        self.assertIn("CALENDAR_CALENDAR_EVIDENCE_MISSING", r["blocks"])
        self.assertIn("CALENDAR_METADATA_INCOMPLETE", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_calendar_mic_mismatch_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            calendar_evidence={"exchange": "XNYS"}, session_date="2026-11-17")
        self.assertIn("CALENDAR_MARKET_MIC_MISMATCH", r["blocks"])
        self.assertFalse(r["notify"])

    def test_complete_calendar_metadata_never_self_attests(self):
        from datetime import datetime, timezone
        now = datetime(2026, 11, 17, 13, tzinfo=timezone.utc)
        calendar = {"session_date": "2026-11-17", "session_kind": "regular",
                    "exchange": "XNAS", "source_url": "https://example.org/calendar",
                    "retrieval_reference": "offline", "retrieved_utc": now.isoformat()}
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            calendar_evidence=calendar, session_date="2026-11-17", now=now)
        self.assertEqual(r["calendar"]["status"], "METADATA_COMPLETE_UNVERIFIED")
        self.assertIn("EXCHANGE_CALENDAR_UNVERIFIED", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_declared_closed_session_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            calendar_evidence={"session_kind": "closed"}, session_date="2026-11-17")
        self.assertIn("CALENDAR_SESSION_CLOSED", r["blocks"])
        self.assertFalse(r["notify"])

    def test_declared_early_close_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL", "mic": "XNAS"},
            calendar_evidence={"session_kind": "early_close"}, session_date="2026-11-17")
        self.assertIn("CALENDAR_EARLY_CLOSE_UNRESOLVED", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_source_instrument_identity_missing_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL"},
            source_identity={"instrument_id": ""})
        self.assertIn("SOURCE_INSTRUMENT_IDENTITY_MISSING", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_source_instrument_identity_unresolved_blocks(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL"},
            source_identity={"instrument_id": "US0378331005"})
        self.assertIn("SOURCE_INSTRUMENT_IDENTITY_UNRESOLVED", r["blocks"])
        self.assertFalse(r["notify"])

    def test_source_instrument_matching_symbol_not_verified(self):
        r = assess_shadow_with_market_evidence(
            {"symbol": "AAPL"}, {"ticker": "AAPL"},
            source_identity={"instrument_id": "aapl"})
        self.assertNotIn("SOURCE_INSTRUMENT_IDENTITY_UNRESOLVED", r["blocks"])
        self.assertIn("SOURCE_INDEPENDENCE_UNVERIFIED", r["blocks"])
        self.assertFalse(r["trade_ready"])

    def test_bad_market_payload_fails_closed(self):
        r = assess_shadow_with_market_evidence({}, {"payload": None})
        self.assertIn("MARKET_EVIDENCE_INVALID", r["blocks"])
        self.assertFalse(r["trade_ready"])

if __name__ == "__main__":
    unittest.main()
