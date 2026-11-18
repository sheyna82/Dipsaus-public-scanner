"""Synthetic cohort denominator and censoring checks."""
import unittest
from research.us_prospective_cohort_accounting_20261118 import audit_prospective_cohort

def entry(symbol, cohort, bars=None, close=99):
    return {"symbol":symbol,"cohort":cohort,
            "snapshot":{"status":"WATCH_UNVERIFIED","snapshot":{
                "symbol":symbol,"historical_friction_usd":100,
                "historical_close_usd":close,
                "source_last_bar_utc":"2026-11-17T20:00:00Z",
                "decision_observed_utc":"2026-11-17T21:00:00Z"}},
            "completed_bars":bars if bars is not None else []}

def bar(end, seen, close):
    return {"bar_end_utc":end,"observed_utc":seen,"close_usd":close}
A=bar("2026-11-17T22:00:00Z","2026-11-17T22:01:00Z",101)
B=bar("2026-11-17T23:00:00Z","2026-11-17T23:01:00Z",100)
C=bar("2026-11-18T00:00:00Z","2026-11-18T00:01:00Z",102)

class CohortAccountingTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(audit_prospective_cohort([])["total_enrolled"],0)

    def test_missing_forward_stays_denominator(self):
        x=audit_prospective_cohort([entry("A","OVERFLOW"),entry("B","OVERFLOW",[A])])
        self.assertEqual(x["by_cohort"]["OVERFLOW"]["enrolled"],2)
        self.assertEqual(x["by_cohort"]["OVERFLOW"]["no_forward_evidence"],1)

    def test_full_retest_count(self):
        x=audit_prospective_cohort([entry("A","REJECTED",[A,B,C])])
        self.assertEqual(x["by_cohort"]["REJECTED"]["retest_reclaim_observed"],1)
        self.assertIsNone(x["verified_profitable_missed_trades"])

    def test_baseline_above_blocked(self):
        x=audit_prospective_cohort([entry("A","PENDING",[A],101)])
        self.assertEqual(x["by_cohort"]["PENDING"]["blocked"],1)

    def test_duplicate_symbol_blocked(self):
        x=audit_prospective_cohort([entry("A","PENDING"),entry("A","OVERFLOW")])
        self.assertEqual(x["status"],"BLOCKED")

    def test_unknown_cohort_blocked(self):
        self.assertEqual(audit_prospective_cohort([entry("A","UNKNOWN")])["status"],"BLOCKED")

    def test_invalid_input(self):
        self.assertEqual(audit_prospective_cohort({})["status"],"BLOCKED")

    def test_missing_symbol(self):
        x=entry("A","PENDING");x["symbol"]=""
        self.assertEqual(audit_prospective_cohort([x])["status"],"BLOCKED")

    def test_no_identifiers_leaked(self):
        x=audit_prospective_cohort([entry("SECRET_SYMBOL","EVALUATED",[A])])
        self.assertNotIn("SECRET_SYMBOL",str(x))

    def test_no_execution_permission(self):
        x=audit_prospective_cohort([entry("A","EVALUATED",[A])])
        self.assertFalse(x["trade_ready"])
        self.assertFalse(x["notify"])
        self.assertFalse(x["order_placement_enabled"])

    def test_invalid_bar_counted_blocked(self):
        x=audit_prospective_cohort([entry("A","EVALUATED",[bar("bad","bad",101)])])
        self.assertEqual(x["by_cohort"]["EVALUATED"]["blocked"],1)

    def test_separate_cohorts(self):
        x=audit_prospective_cohort([entry("A","EVALUATED",[A]),entry("B","OVERFLOW")])
        self.assertEqual(x["by_cohort"]["EVALUATED"]["breakout_observed"],1)
        self.assertEqual(x["by_cohort"]["OVERFLOW"]["breakout_observed"],0)

if __name__=="__main__":
    unittest.main()
