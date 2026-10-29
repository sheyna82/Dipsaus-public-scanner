import unittest
from candidate_portfolio_capacity import simulate, compare_ablation_portfolios

class PortfolioCapacityTests(unittest.TestCase):
    def test_six_position_cap_and_no_same_day_reuse(self):
        signals=[{"symbol":f"S{i}","entry_day":1,"exit_day":3,"net_return_pct":10} for i in range(7)]
        signals.append({"symbol":"LATE","entry_day":3,"exit_day":5,"net_return_pct":10})
        result=simulate(signals)
        self.assertEqual(result["accepted_n"],6)
        self.assertEqual(result["rejection_reasons"]["CAPACITY_FULL"],2)
        self.assertEqual(result["max_concurrent_positions"],6)
        self.assertEqual(result["realized_pnl"],2100)
        self.assertFalse(result["trade_ready"])

    def test_next_day_reuse(self):
        rows=[{"symbol":"A","entry_day":1,"exit_day":2,"net_return_pct":0},
              {"symbol":"B","entry_day":3,"exit_day":4,"net_return_pct":0}]
        self.assertEqual(simulate(rows,max_positions=1,capital=3500)["accepted_n"],2)

    def test_deterministic_tie_break(self):
        rows=[{"symbol":s,"entry_day":1,"exit_day":2,"net_return_pct":0} for s in ("Z","A")]
        self.assertEqual(simulate(rows,max_positions=1)["accepted_signals"][0]["symbol"],"A")

    def test_real_dated_ablation_events_are_pooled_by_filter(self):
        def candidate(symbol, day, selected):
            base={"entry_day":day,"exit_day":day+10,"net_return_pct":5}
            return {"symbol":symbol,"patterns":{"breakout_prior20":{
                "status":"DESCRIPTIVE_ONLY",
                "portfolio_events_25bps":{"baseline":[base],"all_three":[base] if selected else []}}}}
        report={"candidates":[candidate("A",100,True),candidate("B",100,False)]}
        result=compare_ablation_portfolios(report,pattern="breakout_prior20",max_positions=1)
        self.assertEqual(result["comparison"]["baseline"]["accepted_n"],1)
        self.assertEqual(result["comparison"]["baseline"]["rejection_reasons"]["CAPACITY_FULL"],1)
        self.assertEqual(result["comparison"]["all_three"]["accepted_n"],1)
        self.assertFalse(result["trade_ready"])

    def test_invalid_duplicate_rejected(self):
        row={"symbol":"A","entry_day":1,"exit_day":2,"net_return_pct":1}
        with self.assertRaises(ValueError):
            simulate([row,row])

if __name__=="__main__":
    unittest.main()
