import unittest
from dipsaus_offline_asof_audit import audit_asof_features


class AsOfAuditTests(unittest.TestCase):
    def test_published_before_signal(self):
        r = audit_asof_features("2026-10-21T16:00:00+02:00", {
            "atr": {"observed_at": "2026-10-20T17:00:00+02:00",
                    "published_at": "2026-10-20T17:05:00+02:00"}})
        self.assertTrue(r["asof_pass"])
        self.assertFalse(r["trade_ready"])

    def test_future_earnings_update_rejected(self):
        r = audit_asof_features("2026-10-21T16:00:00+02:00", {
            "earnings": {"observed_at": "2026-10-20T10:00:00+02:00",
                         "published_at": "2026-10-22T10:00:00+02:00"}})
        self.assertFalse(r["asof_pass"])
        self.assertEqual(r["rejected_features"][0]["reason"], "future_publication")

    def test_timezone_normalization(self):
        r = audit_asof_features("2026-10-21T14:00:00+00:00", {
            "price": {"observed_at": "2026-10-21T15:00:00+02:00",
                      "published_at": "2026-10-21T15:30:00+02:00"}})
        self.assertTrue(r["asof_pass"])

    def test_naive_or_invalid_timestamp_rejected(self):
        self.assertIsNone(audit_asof_features("2026-10-21T14:00:00", {"x": {}}))
        r = audit_asof_features("2026-10-21T14:00:00+00:00", {
            "x": {"observed_at": "not-a-date",
                  "published_at": "2026-10-20T14:00:00+00:00"}})
        self.assertFalse(r["asof_pass"])


if __name__ == "__main__":
    unittest.main()
