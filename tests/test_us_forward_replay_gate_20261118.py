"""Synthetic forward-only replay tests."""
import unittest
from research.us_forward_replay_gate_20261118 import replay_forward

def snapshot():
    return {"status": "WATCH_UNVERIFIED", "snapshot": {
        "symbol": "SYNTH", "historical_friction_usd": 100,
        "decision_observed_utc": "2026-11-17T21:00:00Z"}}

def bars(prices, start=22):
    return [{"observed_utc": "2026-11-17T%02d:00:00Z" % (start+i),
             "close_usd": p} for i, p in enumerate(prices)]

class ForwardReplayTests(unittest.TestCase):
    def test_no_future_bars(self):
        self.assertEqual(replay_forward(snapshot(), [])["status"], "NO_FORWARD_EVIDENCE")

    def test_forward_sequence(self):
        x = replay_forward(snapshot(), bars([99, 101]))
        self.assertEqual(x["status"], "FORWARD_RESEARCH_ONLY")
        self.assertEqual(x["pattern_status"], "BREAKOUT_OBSERVED")
        self.assertFalse(x["trade_ready"])

    def test_pre_snapshot_rejected(self):
        self.assertEqual(replay_forward(snapshot(), bars([101], start=20))["status"], "BLOCKED")

    def test_same_timestamp_rejected(self):
        self.assertEqual(replay_forward(snapshot(), bars([101], start=21))["status"], "BLOCKED")

    def test_unverified_snapshot_rejected(self):
        x = snapshot(); x["status"] = "BLOCKED"
        self.assertEqual(replay_forward(x, bars([101]))["status"], "BLOCKED")

    def test_missing_snapshot_rejected(self):
        self.assertEqual(replay_forward(None, bars([101]))["status"], "BLOCKED")

    def test_naive_observation_rejected(self):
        self.assertEqual(replay_forward(snapshot(), [{"observed_utc": "2026-11-17T22:00:00", "close_usd": 101}])["status"], "BLOCKED")

    def test_out_of_order_rejected(self):
        x = replay_forward(snapshot(), bars([101, 99], start=22)[::-1])
        self.assertEqual(x["status"], "BLOCKED")

    def test_bad_price_rejected(self):
        self.assertEqual(replay_forward(snapshot(), bars([-1]))["status"], "BLOCKED")

    def test_no_future_profit_claim(self):
        x = replay_forward(snapshot(), bars([101]))
        self.assertNotIn("profit", x)
        self.assertIn("NO_EXECUTION_ECONOMICS", x["blocks"])

if __name__ == "__main__":
    unittest.main()
