"""Calendar metadata cannot self-attest official exchange sessions."""
import unittest
from datetime import datetime, timezone, timedelta
from research.us_exchange_calendar_evidence_20261117 import review_exchange_calendar

class CalendarEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
        self.record = {"session_date": "2026-11-17", "session_kind": "regular",
                       "exchange": "XNAS", "source_url": "https://example.org/calendar",
                       "retrieval_reference": "offline-fixture",
                       "retrieved_utc": self.now.isoformat()}
    def check(self, record=None, **kwargs):
        return review_exchange_calendar(self.record if record is None else record,
                                        session_date=kwargs.pop("session_date", "2026-11-17"),
                                        now=self.now, **kwargs)
    def test_complete_metadata_still_unverified(self):
        r = self.check()
        self.assertEqual(r["status"], "METADATA_COMPLETE_UNVERIFIED")
        self.assertFalse(r["exchange_calendar_verified"])
        self.assertFalse(r["trade_ready"])
    def test_missing_record(self):
        self.assertIn("CALENDAR_EVIDENCE_MISSING", self.check(None if False else {})["blocks"] if False else review_exchange_calendar(None, session_date="2026-11-17", now=self.now)["blocks"])
    def test_wrong_date(self):
        self.assertIn("SESSION_DATE_MISMATCH", self.check(session_date="2026-11-18")["blocks"])
    def test_unknown_session_kind(self):
        self.assertIn("SESSION_KIND_UNSUPPORTED", self.check({**self.record, "session_kind": "holiday?"})["blocks"])
    def test_unknown_exchange(self):
        self.assertIn("EXCHANGE_UNSUPPORTED", self.check({**self.record, "exchange": "XXXX"})["blocks"])
    def test_http_source(self):
        self.assertIn("SOURCE_URL_INVALID", self.check({**self.record, "source_url": "http://example.org"})["blocks"])
    def test_url_missing_host(self):
        self.assertIn("SOURCE_URL_INVALID", self.check({**self.record, "source_url": "https://"})["blocks"])
    def test_url_embedded_credentials(self):
        self.assertIn("SOURCE_URL_INVALID", self.check({**self.record, "source_url": "https://user:pass@example.org/calendar"})["blocks"])
    def test_url_fragment(self):
        self.assertIn("SOURCE_URL_INVALID", self.check({**self.record, "source_url": "https://example.org/calendar#fake"})["blocks"])
    def test_url_malformed_ipv6(self):
        self.assertIn("SOURCE_URL_INVALID", self.check({**self.record, "source_url": "https://[broken/calendar"})["blocks"])
    def test_stale_retrieval(self):
        self.assertIn("RETRIEVAL_STALE_OR_INVALID", self.check({**self.record, "retrieved_utc": (self.now-timedelta(days=30)).isoformat()})["blocks"])
    def test_missing_reference(self):
        self.assertIn("RETRIEVAL_REFERENCE_MISSING", self.check({**self.record, "retrieval_reference": ""})["blocks"])


    def test_claimed_verified_flag_cannot_authorize(self):
        r = self.check({**self.record, "officially_verified": True,
                        "exchange_calendar_verified": True, "trade_ready": True})
        self.assertFalse(r["exchange_calendar_verified"])
        self.assertFalse(r["trade_ready"])
    def test_future_retrieval_beyond_clock_tolerance(self):
        r = self.check({**self.record,
                        "retrieved_utc": (self.now+timedelta(minutes=2)).isoformat()})
        self.assertIn("RETRIEVAL_STALE_OR_INVALID", r["blocks"])
    def test_unparseable_retrieval(self):
        r = self.check({**self.record, "retrieved_utc": "not-a-timestamp"})
        self.assertIn("RETRIEVAL_STALE_OR_INVALID", r["blocks"])
    def test_closed_session_metadata_not_a_trading_authorization(self):
        r = self.check({**self.record, "session_kind": "closed"})
        self.assertFalse(r["exchange_calendar_verified"])
        self.assertFalse(r["trade_ready"])

if __name__ == "__main__":
    unittest.main()
