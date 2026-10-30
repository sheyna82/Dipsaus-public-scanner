"""Deterministic checks for quarterly diagnostics (no data download)."""
import unittest
from candidate_portfolio_quarter_diagnostics import summarize


class QuarterDiagnosticsTests(unittest.TestCase):
    def test_quarters_use_entry_day_and_accepted_trades_only(self):
        from datetime import date
        def day(y,m,d):
            return (date(y,m,d)-date(1970,1,1)).days
        portfolio={"tranche":3500.0,"accepted_signals":[
            {"symbol":"AAA","entry_day":day(2026,3,31),"exit_day":day(2026,4,15),
             "net_return_pct":2.0},
            {"symbol":"BBB","entry_day":day(2026,4,1),"exit_day":day(2026,4,16),
             "net_return_pct":-1.0},
            {"symbol":"AAA","entry_day":day(2026,4,20),"exit_day":day(2026,5,4),
             "net_return_pct":3.0},
        ]}
        result=summarize({"portfolio_oos":{"recovery":{
            "baseline":portfolio,"filtered":{"tranche":3500.0,"accepted_signals":[]}}}})
        base=result["patterns"]["recovery"]["baseline"]
        self.assertEqual(base["quarters"]["2026Q1"]["accepted_n"],1)
        self.assertEqual(base["quarters"]["2026Q1"]["realized_pnl_approx"],70.0)
        self.assertEqual(base["quarters"]["2026Q2"]["realized_pnl_approx"],70.0)
        self.assertEqual(base["positive_quarters"],2)
        self.assertEqual(base["top_symbols_by_accepted_count"][0],("AAA",2))
        self.assertEqual(result["patterns"]["recovery"]["filtered"]["positive_quarters"],0)
        self.assertFalse(result["trade_ready"])

    def test_empty_patterns(self):
        self.assertEqual(summarize({"portfolio_oos":{}})["patterns"],{})


if __name__=="__main__":
    unittest.main()
