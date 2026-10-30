import unittest
from dipsaus_offline_event_session_gate import check_daily_session


class SessionGateTests(unittest.TestCase):
    def test_completed_session_match(self):
        result = check_daily_session("2026-10-21", "2026-10-21",
                                     provider_verified=True)
        self.assertEqual(result["status"], "SESSION_MATCH")
        self.assertFalse(result["trade_ready"])

    def test_stale_session_blocked(self):
        self.assertEqual(check_daily_session("2026-10-20", "2026-10-21",
                         provider_verified=True)["reason"], "unexpected_completed_session")

    def test_unverified_provider_blocked(self):
        self.assertEqual(check_daily_session("2026-10-21", "2026-10-21")["status"],
                         "DATA_BLOCKED")

    def test_invalid_date_blocked(self):
        self.assertEqual(check_daily_session("2026-02-30", "2026-10-21",
                         provider_verified=True)["status"], "DATA_BLOCKED")

    def test_noncanonical_date_blocked(self):
        self.assertEqual(check_daily_session("2026-1-2", "2026-1-2",
                         provider_verified=True)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
