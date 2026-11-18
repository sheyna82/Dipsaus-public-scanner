"""Synthetic completed-bar provenance tests."""
import unittest
from research.us_strict_forward_evidence_20261118 import evaluate_strict_forward

def snap(close=99):
    return {"status":"WATCH_UNVERIFIED","snapshot":{
        "symbol":"SYNTH","historical_friction_usd":100,
        "historical_close_usd":close,"source_last_bar_utc":"2026-11-17T20:00:00Z",
        "decision_observed_utc":"2026-11-17T21:00:00Z"}}

def bar(end, observed, price):
    return {"bar_end_utc":end,"observed_utc":observed,"close_usd":price}

A=bar("2026-11-17T22:00:00Z","2026-11-17T22:01:00Z",101)
B=bar("2026-11-17T23:00:00Z","2026-11-17T23:01:00Z",100)
C=bar("2026-11-18T00:00:00Z","2026-11-18T00:01:00Z",102)

class StrictForwardTests(unittest.TestCase):
    def test_breakout_after_below_baseline(self):
        x=evaluate_strict_forward(snap(),[A])
        self.assertEqual(x["pattern_status"],"BREAKOUT_OBSERVED")
        self.assertFalse(x["trade_ready"])

    def test_already_above_not_new_breakout(self):
        self.assertEqual(evaluate_strict_forward(snap(101),[A])["status"],
                         "BASELINE_ALREADY_AT_OR_ABOVE_FRICTION")

    def test_at_level_not_new_breakout(self):
        self.assertEqual(evaluate_strict_forward(snap(100),[A])["status"],
                         "BASELINE_ALREADY_AT_OR_ABOVE_FRICTION")

    def test_full_retest(self):
        x=evaluate_strict_forward(snap(),[A,B,C])
        self.assertEqual(x["pattern_status"],"RESEARCH_REVIEW")
        self.assertFalse(x["order_placement_enabled"])

    def test_no_future(self):
        self.assertEqual(evaluate_strict_forward(snap(),[])["status"],"NO_FORWARD_EVIDENCE")

    def test_bar_before_cutoff(self):
        x=evaluate_strict_forward(snap(),[bar("2026-11-17T20:30:00Z","2026-11-17T22:00:00Z",101)])
        self.assertEqual(x["status"],"BLOCKED")

    def test_bar_end_after_observation(self):
        x=evaluate_strict_forward(snap(),[bar("2026-11-17T23:00:00Z","2026-11-17T22:00:00Z",101)])
        self.assertEqual(x["status"],"BLOCKED")

    def test_duplicate_bar(self):
        self.assertEqual(evaluate_strict_forward(snap(),[A,A])["status"],"BLOCKED")

    def test_nonmonotonic_bars(self):
        self.assertEqual(evaluate_strict_forward(snap(),[B,A])["status"],"BLOCKED")

    def test_naive_observed(self):
        x=evaluate_strict_forward(snap(),[bar("2026-11-17T22:00:00Z","2026-11-17T22:01:00",101)])
        self.assertEqual(x["status"],"BLOCKED")

    def test_boolean_price(self):
        x=evaluate_strict_forward(snap(),[bar("2026-11-17T22:00:00Z","2026-11-17T22:01:00Z",True)])
        self.assertEqual(x["status"],"BLOCKED")

    def test_unverified_snapshot(self):
        x=snap();x["status"]="BLOCKED"
        self.assertEqual(evaluate_strict_forward(x,[A])["status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
