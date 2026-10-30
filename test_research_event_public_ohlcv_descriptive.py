import unittest
from pathlib import Path
from research_event_public_ohlcv_descriptive import analyze_public_observations

class PublicOhlcvTests(unittest.TestCase):
    def test_all_four_have_descriptive_downside(self):
        path = Path(__file__).with_name("research_event_public_ohlcv_observations_202610.csv")
        result = analyze_public_observations(path)
        self.assertEqual({x["symbol"] for x in result}, {"TSLA","META","COHU","AMZN"})
        self.assertTrue(all(not x["signal_predictive_edge_proven"] for x in result))
        self.assertTrue(all(float(x["worst_observed_intraday_vs_baseline_pct"]) < 0 for x in result))

if __name__ == "__main__":
    unittest.main()
