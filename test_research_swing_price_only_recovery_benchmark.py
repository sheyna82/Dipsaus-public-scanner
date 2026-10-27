import unittest
from research_swing_price_only_recovery_benchmark import recovery_vs_unconditional

def bars():
    closes = [100, 100, 100, 90, 85, 84, 86, 88, 90, 92, 94, 96, 98, 100]
    return [{"open_at": f"2026-01-{i+1:02d}T09:30:00Z",
             "close_at": f"2026-01-{i+1:02d}T16:00:00Z",
             "open": float(v), "high": float(v+1), "low": float(v-1),
             "close": float(v)} for i, v in enumerate(closes)]

class PriceOnlyBenchmarkTests(unittest.TestCase):
    def test_recovery_signal_and_baseline(self):
        result = recovery_vs_unconditional({"X": bars()}, horizons=(3,), lookback=3, dip_pct=10)
        cohort = result["horizons"]["3"]
        self.assertGreater(cohort["signal_trades"], 0)
        self.assertGreater(cohort["baseline_observations_overlapping"], cohort["signal_trades"])
        self.assertFalse(result["predictive_edge_proven"])
    def test_no_signal_does_not_invent_return(self):
        result = recovery_vs_unconditional({"X": bars()}, horizons=(3,), lookback=3, dip_pct=90)
        self.assertIsNone(result["horizons"]["3"]["signal_mean_net_pct"])
    def test_cost_reduces_returns(self):
        x = recovery_vs_unconditional({"X": bars()}, horizons=(3,), lookback=3, dip_pct=10, cost_bps=0)
        y = recovery_vs_unconditional({"X": bars()}, horizons=(3,), lookback=3, dip_pct=10, cost_bps=100)
        self.assertAlmostEqual(x["horizons"]["3"]["signal_mean_net_pct"] -
                               y["horizons"]["3"]["signal_mean_net_pct"], 1.0)
    def test_rejects_invalid_bars(self):
        data = bars()
        data[0]["low"] = 200
        with self.assertRaisesRegex(ValueError, "inconsistent_ohlc"):
            recovery_vs_unconditional({"X": data})

if __name__ == "__main__":
    unittest.main()
