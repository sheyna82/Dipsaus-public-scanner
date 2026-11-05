import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dipsaus_offline_exe_isolated_replay import replay_isolated_spans


class IsolatedReplayTests(unittest.TestCase):
    def test_gap_resets_history(self):
        start = datetime(2026, 10, 21, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        stamps = [int((start+timedelta(minutes=i)).timestamp()) for i in range(70)]
        quote = {"open": [100.]*70, "high": [101.]*70,
                 "low": [99.]*70, "close": [100.]*70}
        quote["close"][35] = None
        result = replay_isolated_spans(stamps, quote, "2026-10-21")
        self.assertEqual([x["bars"] for x in result["spans"]], [35, 34])
        self.assertTrue(result["history_resets_at_gaps"])
        self.assertFalse(result["full_session_replay_permitted"])
        self.assertEqual(result["rejected_bars"], 1)


if __name__ == "__main__":
    unittest.main()
