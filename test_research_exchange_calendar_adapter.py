import hashlib
import json
import unittest
from research_exchange_calendar_adapter import audit_calendar_export


class ExchangeCalendarAdapterTests(unittest.TestCase):
    def export(self, sessions):
        canonical = json.dumps(sessions, separators=(",", ":"), ensure_ascii=True)
        return {"exchange": "XNYS", "calendar_library": "exchange_calendars",
                "calendar_version": "UNVERIFIED_TEST_FIXTURE",
                "session_dates": sessions, "source_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
                "digest_scope": "canonical_session_dates_json"}

    def test_us_weekend_and_holiday_fixture(self):
        # Fixture is illustrative; not claimed to be upstream calendar output.
        sessions = ["2025-01-17", "2025-01-21", "2025-01-22"]
        r = audit_calendar_export(["2025-01-17", "2025-01-22"],
                                  self.export(sessions))
        self.assertEqual(r["missing_expected_sessions"], ["2025-01-21"])
        self.assertFalse(r["calendar_provenance_verified"])

    def test_european_fixture(self):
        item = self.export(["2025-04-17", "2025-04-22"])
        item["exchange"] = "XAMS"
        r = audit_calendar_export(["2025-04-17", "2025-04-22"], item)
        self.assertTrue(r["complete_against_supplied_calendar"])

    def test_rejects_unchecked_digest_scope(self):
        item = self.export(["2025-04-17", "2025-04-22"])
        del item["digest_scope"]
        with self.assertRaisesRegex(ValueError, "unverified_calendar_digest_scope"):
            audit_calendar_export(["2025-04-17", "2025-04-22"], item)

    def test_rejects_missing_digest(self):
        item = self.export(["2025-04-17", "2025-04-22"])
        item["source_sha256"] = ""
        with self.assertRaisesRegex(ValueError, "missing_calendar_provenance"):
            audit_calendar_export(["2025-04-17", "2025-04-22"], item)


if __name__ == "__main__":
    unittest.main()
