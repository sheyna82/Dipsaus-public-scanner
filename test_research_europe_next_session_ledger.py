import unittest
from research_europe_next_session_ledger import simulate

def bars(prices):
    return [{"day":f"2026-11-{i+1:02d}","open":v,"close":v} for i,v in enumerate(prices)]

class LedgerTests(unittest.TestCase):
    def test_next_session_and_whole_shares(self):
        r=simulate({"A":bars([100,110,120,130])},[{"symbol":"A","day":"2026-11-01"}],hold_sessions=2)
        t=r["trades"][0]
        self.assertEqual(t["entry_day"],"2026-11-02")
        self.assertEqual(t["exit_day"],"2026-11-03")
        self.assertIsInstance(t["shares"],int)
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["orders_placed"])
    def test_no_future_exit_no_trade(self):
        r=simulate({"A":bars([100,110])},[{"symbol":"A","day":"2026-11-01"}],hold_sessions=2)
        self.assertEqual(r["trade_count"],0)
    def test_cash_blocks(self):
        r=simulate({"A":bars([100,100,100])},[{"symbol":"A","day":"2026-11-01"}],
                   initial_cash=5,hold_sessions=1)
        self.assertEqual(r["trade_count"],0)
    def test_same_symbol_overlap(self):
        r=simulate({"A":bars([100]*6)},[{"symbol":"A","day":"2026-11-01"},
                   {"symbol":"A","day":"2026-11-02"}],hold_sessions=3)
        self.assertEqual(r["trade_count"],1)
    def test_invalid_price_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"INVALID_PRICE"):
            simulate({"A":bars([100,0,110])},[])
    def test_no_fractional_shares(self):
        r=simulate({"A":bars([100,2000,2000])},[{"symbol":"A","day":"2026-11-01"}],hold_sessions=1)
        self.assertEqual(r["trades"][0]["shares"],1)
if __name__=="__main__":unittest.main()
