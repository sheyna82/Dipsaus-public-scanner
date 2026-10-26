import unittest
from research_swing_portfolio_proxy import portfolio_swing_proxy

class PortfolioProxyTests(unittest.TestCase):
    def panel(self):
        return {s:[{"timestamp":i,"open":100,"high":101,"low":99,"close":100}
                   for i in range(75)] for s in ("A","B","C","D","E","F","G")}

    def test_cash_and_slot_limit(self):
        result=portfolio_swing_proxy(self.panel(),horizon=5,slots=3)
        self.assertLessEqual(result["max_simultaneous_positions"],3)
        self.assertAlmostEqual(result["total_net_return_pct"],-.3,delta=1.5)
        self.assertFalse(result["trade_ready"])

    def test_misaligned_panel_rejected(self):
        bars=self.panel()
        bars["A"][10]["timestamp"]=999
        with self.assertRaises(ValueError):
            portfolio_swing_proxy(bars)

    def test_warning_exits_are_optional(self):
        bars=self.panel()
        bars["A"][26]={"timestamp":26,"open":92,"high":93,"low":88,"close":90}
        base=portfolio_swing_proxy(bars,horizon=10,warning_exits=False)
        warned=portfolio_swing_proxy(bars,horizon=10,warning_exits=True)
        self.assertEqual(base["warning_exit_trades"],0)
        self.assertGreaterEqual(warned["warning_exit_trades"],0)

if __name__=="__main__":
    unittest.main()
