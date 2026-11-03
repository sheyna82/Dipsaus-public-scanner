import unittest
from datetime import datetime, timedelta, timezone
from research.us_setup_archive_coverage import audit_archive


class ArchiveCoverageTests(unittest.TestCase):
    def setUp(self):
        t = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        self.rows = [{"ts": (t + timedelta(minutes=i)).timestamp(),
                      "low": 99, "close": 100} for i in range(25)]

    def test_empty_archive_not_oos(self):
        result = audit_archive({})
        self.assertEqual(result["reason"], "NO_ARCHIVED_SESSIONS")
        self.assertFalse(result["oos_eligible"])

    def test_one_session_insufficient(self):
        result = audit_archive({"CSGP|2026-10-01": self.rows})
        self.assertEqual(result["session_count"], 1)
        self.assertEqual(result["reason"], "INSUFFICIENT_ARCHIVED_SESSIONS")

    def test_wrong_day_rejected(self):
        result = audit_archive({"CSGP|2026-10-02": self.rows})
        self.assertEqual(result["rejected_reasons"]["SESSION_DATE_MISMATCH_UTC"], 1)

    def test_many_sessions_do_not_prove_label_independence(self):
        archive = {}
        for i in range(21):
            shifted = [{**bar, "ts": bar["ts"] + 86400*i} for bar in self.rows]
            day = (datetime(2026, 10, 1) + timedelta(days=i)).date().isoformat()
            archive["CSGP|" + day] = shifted
        result = audit_archive(archive)
        self.assertEqual(result["session_count"], 21)
        self.assertFalse(result["oos_eligible"])
        self.assertFalse(result["labels_independent_verified"])

    def test_daily_series_rejected(self):
        t = datetime(2026, 10, 1, tzinfo=timezone.utc)
        rows = [{**bar, "ts": (t + timedelta(days=i)).timestamp()}
                for i, bar in enumerate(self.rows)]
        result = audit_archive({"CSGP|2026-10-01": rows})
        self.assertEqual(result["session_count"], 0)


if __name__ == "__main__":
    unittest.main()
