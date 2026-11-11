import hashlib
import json
import sys
import types
import unittest
from unittest.mock import patch

from research_exchange_calendar_local_export import export_sessions
from research_exchange_calendar_adapter import audit_calendar_export


class FakeSession:
    def __init__(self, value):
        from datetime import date
        self.value = date.fromisoformat(value)

    def date(self):
        return self.value


class CalendarExportTests(unittest.TestCase):
    def test_export_roundtrip_and_tamper_detection(self):
        fake = types.SimpleNamespace(
            __version__="4.13.2",
            get_calendar=lambda name: types.SimpleNamespace(
                sessions_in_range=lambda start, end: [
                    FakeSession("2025-01-17"), FakeSession("2025-01-21")]))
        with patch.dict(sys.modules, {"exchange_calendars": fake}):
            result = export_sessions("XNYS", "2025-01-17", "2025-01-21")
        audit = audit_calendar_export(["2025-01-17", "2025-01-21"], result)
        self.assertTrue(audit["calendar_export_digest_verified"])
        self.assertFalse(audit["calendar_provenance_verified"])
        result["session_dates"][1] = "2025-01-22"
        with self.assertRaisesRegex(ValueError, "calendar_digest_mismatch"):
            audit_calendar_export(["2025-01-17", "2025-01-22"], result)

    def test_rejects_unpinned_version(self):
        with patch.dict(sys.modules, {"exchange_calendars":
                                     types.SimpleNamespace(__version__="0.0")}):
            with self.assertRaisesRegex(ValueError, "unreviewed_calendar_version"):
                export_sessions("XAMS", "2025-01-01", "2025-01-02")


if __name__ == "__main__":
    unittest.main()
