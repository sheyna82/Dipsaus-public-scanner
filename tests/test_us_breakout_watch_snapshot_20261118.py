"""Synthetic point-in-time contract tests, no private scanner data."""
import unittest
from research.us_breakout_watch_snapshot_20261118 import build_watch_snapshot

BAR = "2026-11-17T21:00:00Z"
SOURCE = "2026-11-17T21:01:00Z"
DECISION = "2026-11-17T21:02:00Z"

def candidate():
    return {"symbol": "SYNTH", "last_close_usd": 99.5,
            "recovery_map": {"first_friction_reference_usd": 100,
                             "resistance_confirmed": False}}

def audit(c=None, **kw):
    args = dict(source_last_bar_utc=BAR, source_observed_utc=SOURCE,
                decision_observed_utc=DECISION, batch_index=7)
    args.update(kw)
    return build_watch_snapshot(candidate() if c is None else c, **args)

class WatchSnapshotTests(unittest.TestCase):
    def test_valid_still_unverified(self):
        x = audit()
        self.assertEqual(x["status"], "WATCH_UNVERIFIED")
        self.assertEqual(x["snapshot"]["historical_friction_usd"], 100)
        for k in ("trade_ready", "notify", "automatic_orders", "order_placement_enabled"):
            self.assertFalse(x[k])

    def test_source_after_decision(self):
        self.assertEqual(audit(decision_observed_utc=BAR)["status"], "BLOCKED")

    def test_bar_after_source(self):
        self.assertEqual(audit(source_last_bar_utc=DECISION)["status"], "BLOCKED")

    def test_naive_time_rejected(self):
        self.assertEqual(audit(source_observed_utc="2026-11-17T21:01:00")["status"], "BLOCKED")

    def test_missing_time_rejected(self):
        self.assertEqual(audit(source_observed_utc=None)["status"], "BLOCKED")

    def test_invalid_batch(self):
        self.assertEqual(audit(batch_index=21)["status"], "BLOCKED")

    def test_boolean_batch(self):
        self.assertEqual(audit(batch_index=True)["status"], "BLOCKED")

    def test_no_friction(self):
        c = candidate()
        c["recovery_map"]["first_friction_reference_usd"] = None
        self.assertEqual(audit(c)["status"], "BLOCKED")

    def test_no_close(self):
        c = candidate()
        c["last_close_usd"] = None
        self.assertEqual(audit(c)["status"], "BLOCKED")

    def test_resistance_claim_blocked(self):
        c = candidate()
        c["recovery_map"]["resistance_confirmed"] = True
        self.assertEqual(audit(c)["status"], "BLOCKED")

    def test_no_recovery_map(self):
        c = candidate()
        c.pop("recovery_map")
        self.assertEqual(audit(c)["status"], "BLOCKED")

    def test_wrong_market(self):
        c = candidate()
        c["market"] = "EU"
        self.assertEqual(audit(c)["status"], "BLOCKED")

    def test_no_future_outcome_claim(self):
        x = audit()
        self.assertNotIn("outcome", x)
        self.assertIn("FUTURE_BREAKOUT_NOT_OBSERVED", x["blocks"])

if __name__ == "__main__":
    unittest.main()
