"""Synthetic-only tests; no private state, broker calls, or real signals."""
import unittest
from research.us_breakout_retest_shadow_20261118 import audit_breakout_retest

T = ["2026-11-16T15:00:00Z", "2026-11-16T16:00:00Z",
     "2026-11-16T17:00:00Z", "2026-11-16T18:00:00Z"]

def record(prices, times=None):
    times = times or T
    return {"symbol": "SYNTH", "historical_friction_usd": 100,
            "observations": [{"observed_utc": t, "close_usd": p}
                             for t, p in zip(times, prices)]}

class BreakoutRetestShadowTests(unittest.TestCase):
    def test_no_observations_is_watch(self):
        x = audit_breakout_retest(record([]))
        self.assertEqual(x["status"], "WATCH_UNVERIFIED")
        self.assertFalse(x["trade_ready"])

    def test_no_breakout(self):
        self.assertEqual(audit_breakout_retest(record([99, 100, 98]))["status"], "WATCH_UNVERIFIED")

    def test_breakout_without_retest(self):
        self.assertEqual(audit_breakout_retest(record([99, 101, 102]))["status"], "BREAKOUT_OBSERVED")

    def test_retest_without_reclaim(self):
        self.assertEqual(audit_breakout_retest(record([99, 101, 100]))["status"], "RETEST_OBSERVED")

    def test_complete_sequence_still_not_trade_ready(self):
        x = audit_breakout_retest(record([99, 101, 100, 102]))
        self.assertEqual(x["status"], "RESEARCH_REVIEW")
        for key in ("trade_ready", "notify", "automatic_orders", "order_placement_enabled"):
            self.assertIs(x[key], False)
        self.assertIn("EUR_NET_PROFIT_UNVERIFIED", x["blocks"])

    def test_same_bar_cannot_prove_retest(self):
        self.assertEqual(audit_breakout_retest(record([99, 101]))["status"], "BREAKOUT_OBSERVED")

    def test_reject_nonmonotonic_time(self):
        x = audit_breakout_retest(record([99, 101], [T[1], T[0]]))
        self.assertEqual(x["status"], "BLOCKED")
        self.assertIn("TIMESTAMP_MISSING_OR_NONMONOTONIC", x["blocks"])

    def test_reject_naive_time(self):
        x = audit_breakout_retest(record([99], ["2026-11-16T15:00:00"]))
        self.assertEqual(x["status"], "BLOCKED")

    def test_reject_invalid_level(self):
        x = audit_breakout_retest({"symbol": "SYNTH", "historical_friction_usd": 0, "observations": []})
        self.assertEqual(x["status"], "BLOCKED")

    def test_reject_bad_close(self):
        x = audit_breakout_retest(record([99, -1]))
        self.assertEqual(x["status"], "BLOCKED")

    def test_reject_missing_symbol(self):
        self.assertEqual(audit_breakout_retest({"historical_friction_usd": 100})["status"], "BLOCKED")

    def test_no_observation_backfill(self):
        x = audit_breakout_retest({"symbol": "SYNTH", "historical_friction_usd": 100})
        self.assertEqual(x["status"], "WATCH_UNVERIFIED")

if __name__ == "__main__":
    unittest.main()
