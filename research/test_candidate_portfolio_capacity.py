import unittest
from candidate_portfolio_capacity import simulate

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

    def test_invalid_duplicate_rejected(self):
        row={"symbol":"A","entry_day":1,"exit_day":2,"net_return_pct":1}
        with self.assertRaises(ValueError):
            simulate([row,row])

if __name__=="__main__":
    unittest.main()
