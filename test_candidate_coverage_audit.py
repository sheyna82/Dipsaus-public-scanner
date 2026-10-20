import unittest
from datetime import datetime, timezone, timedelta
from candidate_coverage_audit import reconcile

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)

def candidate(cid, status="ACTIVE"):
    return {"id": cid, "status": status}

def obs(cid, status="FRESH_CHECKED", at=NOW, reason=None):
    return {"candidate_id": cid, "status": status,
            "checked_at": at.isoformat(), "reason": reason}

class CoverageAuditTests(unittest.TestCase):
    def test_future_dated_evidence_never_counts_as_fresh(self):
        future = NOW + timedelta(seconds=1)
        result = reconcile([candidate("A")], [obs("A", at=future)], now=NOW)
        self.assertEqual(result["summary"]["fresh_checked"], 0)
        self.assertEqual(result["summary"]["overdue"], 1)

    def test_invalid_freshness_window_rejected(self):
        for value in (True, float("inf"), float("nan"), -1, 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile([candidate("A")], [], now=NOW,
                          max_age_seconds=value)

    def test_closed_candidate_excluded_from_active_coverage(self):
        result = reconcile(
            [{"id":"old","status":"CLOSED"},
             {"id":"new","status":"ACTIVE"}], [])
        self.assertEqual(result["summary"]["active"],1)
        self.assertEqual(result["summary"]["overdue"],1)
        self.assertEqual([r["candidate_id"] for r in result["private_details"]],["new"])

    def test_duplicate_id_closed_and_active_is_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([{"id":"A","status":"CLOSED"},
                       {"id":"A","status":"ACTIVE"}], [])

    def test_complete(self):
        r = reconcile([candidate("a"), candidate("b")],
            [obs("a"), obs("b", "DEFERRED", reason="MARKET_CLOSED")], now=NOW)
        self.assertTrue(r["summary"]["reconciled"])
        self.assertEqual(r["summary"]["deferred"], 1)

    def test_missing_candidate_never_disappears(self):
        r = reconcile([candidate("a"), candidate("b")], [obs("a")], now=NOW)
        self.assertEqual(r["summary"]["overdue"], 1)
        self.assertFalse(r["summary"]["reconciled"])

    def test_stale_data_is_not_fresh(self):
        r = reconcile([candidate("a")], [obs("a", at=NOW-timedelta(minutes=20))], now=NOW)
        self.assertEqual(r["summary"]["overdue"], 1)

    def test_blocked_needs_reason(self):
        r = reconcile([candidate("a")], [obs("a", "DATA_BLOCKED")], now=NOW)
        self.assertFalse(r["summary"]["reconciled"])

    def test_closed_excluded(self):
        r = reconcile([candidate("a", "CLOSED")], [], now=NOW)
        self.assertEqual(r["summary"]["active"], 0)

    def test_duplicate_candidate_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([candidate("a"), candidate("a")], [], now=NOW)

    def test_duplicate_observation_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([candidate("a")], [obs("a"), obs("a")], now=NOW)

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([], [], now=datetime(2026, 10, 20))

if __name__ == "__main__":
    unittest.main()
