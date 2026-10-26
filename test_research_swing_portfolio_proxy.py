import unittest
from research_swing_portfolio_proxy import portfolio_swing_proxy

class PortfolioProxyTests(unittest.TestCase):
    def panel(self):
        return {s:[{"timestamp":i,"open":100,"high":101,"low":99,"close":100}
                   for i in range(75)] for s in ("A","B","C","D","E","F","G")}

    def test_cash_and_slot_limit(self):
        result=portfolio_swing_proxy(self.panel(),horizon=5,slots=3)
        self.assertLessEqual(result["max_simultaneous_positions"],3)
        self.assertLessEqual(result["peak_committed_capital_pct"],100.0001)
        # Repeated five-session trades incur costs on every round trip.
        self.assertLess(result["total_net_return_pct"],-.3)
        self.assertGreater(result["completed_trades"],3)
        self.assertAlmostEqual(result["worst_completed_trade_pct"],-.3,delta=.001)
        self.assertEqual(sum(result["completed_loss_buckets"].values()),0)
        self.assertFalse(result["trade_ready"])

    def test_adverse_slippage_reduces_net_return(self):
        bars=self.panel()
        base=portfolio_swing_proxy(bars,horizon=5,slots=3,slippage_bps=0)
        adverse=portfolio_swing_proxy(bars,horizon=5,slots=3,slippage_bps=20)
        self.assertLess(adverse["total_net_return_pct"],base["total_net_return_pct"])
        self.assertEqual(adverse["slippage_bps_per_side"],20)

    def test_invalid_slippage_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid_cost_or_cash"):
            portfolio_swing_proxy(self.panel(),slippage_bps=-1)

    def test_cash_reserve_cap(self):
        result=portfolio_swing_proxy(self.panel(),horizon=5,slots=6,max_exposure_fraction=.5)
        self.assertLessEqual(result["peak_committed_capital_pct"],50.0001)
        self.assertEqual(result["max_exposure_fraction"],.5)

    def test_misaligned_panel_rejected(self):
        bars=self.panel()
        bars["A"][10]["timestamp"]=999
        with self.assertRaises(ValueError):
            portfolio_swing_proxy(bars)

    def test_inconsistent_ohlc_is_rejected(self):
        bars=self.panel()
        bars["A"][25]["open"]=120
        with self.assertRaisesRegex(ValueError,"inconsistent_ohlc"):
            portfolio_swing_proxy(bars)

    def test_simultaneous_decline_severity_is_measured(self):
        bars=self.panel()
        for rows in bars.values():
            rows[30]={"timestamp":30,"open":100,"high":101,"low":94,"close":95}
        result=portfolio_swing_proxy(bars,horizon=15,slots=3)
        self.assertGreater(result["days_with_majority_positions_declining"],0)
        self.assertLess(result["worst_equity_change_majority_declining_pct"],0)
        self.assertLess(result["mean_equity_change_majority_declining_pct"],0)
        self.assertLess(result["worst_daily_equity_move_pct"],0)

    def test_market_regime_loss_buckets_are_consistent(self):
        bars=self.panel()
        for rows in bars.values():
            rows[45]={"timestamp":45,"open":100,"high":101,"low":94,"close":95}
        result=portfolio_swing_proxy(bars,horizon=15,slots=3)
        two=result["market_proxy_regime_days_loss_2pct_or_more"]
        four=result["market_proxy_regime_days_loss_4pct_or_more"]
        negative=result["market_proxy_regime_negative_days"]
        for regime in ("uptrend","downtrend","unknown"):
            self.assertLessEqual(four[regime],two[regime])
            self.assertLessEqual(two[regime],negative[regime])
        self.assertGreater(sum(two.values()),0)

    def test_sector_cap_restricts_correlated_entries(self):
        symbols=("AMD","META","XOM","CVX","KO","PG","JPM","BAC")
        bars={s:[{"timestamp":i,"open":100,"high":101,"low":99,"close":100}
                 for i in range(75)] for s in symbols}
        result=portfolio_swing_proxy(bars,horizon=10,slots=6,max_positions_per_sector=1)
        self.assertLessEqual(result["peak_same_sector_positions"],1)
        self.assertEqual(result["max_positions_per_sector"],1)
        self.assertGreater(result["completed_trades"],0)

    def test_sector_cap_requires_known_sector(self):
        with self.assertRaisesRegex(ValueError,"unmapped_sector"):
            portfolio_swing_proxy(self.panel(),max_positions_per_sector=1)

    def test_delayed_entry_starts_after_holdout_boundary(self):
        bars=self.panel()
        early=portfolio_swing_proxy(bars,horizon=10,slots=3)
        late=portfolio_swing_proxy(bars,horizon=10,slots=3,entry_start_index=55)
        self.assertEqual(late["entry_start_index"],55)
        self.assertLess(late["completed_trades"],early["completed_trades"])
        self.assertGreater(late["completed_trades"],0)

    def test_invalid_delayed_entry_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid_entry_start_index"):
            portfolio_swing_proxy(self.panel(),entry_start_index=75)

    def test_future_bars_cannot_change_past_executed_trades(self):
        # Inspired by Freqtrade's lookahead-analysis: change unseen future
        # candles and require all earlier completed trades to stay identical.
        bars=self.panel()
        for symbol,rows in bars.items():
            for i in range(21,75):
                close=100 + (i % 9) * (1 if symbol in ("A","C","E") else -1)
                rows[i]={"timestamp":i,"open":close,"high":close+2,
                         "low":close-2,"close":close}
        baseline=portfolio_swing_proxy(bars,horizon=10,slots=3,warning_exits=True)
        changed={symbol:[dict(row) for row in rows] for symbol,rows in bars.items()}
        for symbol,rows in changed.items():
            for i in range(60,75):
                price=150 if symbol in ("A","C","E") else 60
                rows[i]={"timestamp":i,"open":price,"high":price+2,
                         "low":price-2,"close":price}
        altered=portfolio_swing_proxy(changed,horizon=10,slots=3,warning_exits=True)
        past=lambda result:[trade for trade in result["trades"] if trade["exit_index"]<60]
        self.assertEqual(past(baseline),past(altered))

    def test_selective_warning_policies_are_supported(self):
        bars=self.panel()
        for policy in ("all","severe_only","breakdown_only"):
            result=portfolio_swing_proxy(bars,horizon=10,warning_exits=True,
                                         warning_policy=policy)
            self.assertEqual(result["warning_policy"],policy)

    def test_unknown_warning_policy_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid_warning_policy"):
            portfolio_swing_proxy(self.panel(),warning_policy="optimized")

    def test_warning_exits_are_optional(self):
        bars=self.panel()
        bars["A"][26]={"timestamp":26,"open":92,"high":93,"low":88,"close":90}
        base=portfolio_swing_proxy(bars,horizon=10,warning_exits=False)
        warned=portfolio_swing_proxy(bars,horizon=10,warning_exits=True)
        self.assertEqual(base["warning_exit_trades"],0)
        self.assertGreaterEqual(warned["warning_exit_trades"],0)

if __name__=="__main__":
    unittest.main()
