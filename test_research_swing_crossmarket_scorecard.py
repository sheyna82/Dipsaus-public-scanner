import unittest
from research_swing_crossmarket_scorecard import research_coverage_scorecard

def row(symbol, event_id, **kwargs):
    data = dict(symbol=symbol, event_id=event_id, market="US",
                sector="technology", cap_bucket="large", regime="bear",
                event_kind="earnings", horizon=5)
    data.update(kwargs)
    return data

class CrossmarketScorecardTests(unittest.TestCase):
    def test_empty_data_cannot_claim_edge(self):
        result = research_coverage_scorecard([])
        self.assertFalse(result["predictive_edge_proven"])
        self.assertEqual(result["total_input_rows"], 0)
    def test_duplicate_horizons_not_counted_as_unique_events(self):
        result = research_coverage_scorecard([row("A", "1"), row("A", "1", horizon=10)])
        self.assertEqual(result["dimensions"]["market"]["US"]["event_count"], 1)
        self.assertEqual(result["dimensions"]["horizon"]["5"]["event_count"], 1)
    def test_multiple_markets_and_regimes(self):
        result = research_coverage_scorecard([row("A", "1"), row("B", "2", market="FR", regime="bull")])
        self.assertIn("FR", result["dimensions"]["market"])
        self.assertIn(("FR", "bull", "5"), result["market_regime_horizon"])
    def test_minimum_independent_symbols(self):
        records = [row("A", str(i)) for i in range(40)]
        result = research_coverage_scorecard(records)
        self.assertFalse(result["dimensions"]["market"]["US"]["sufficient_for_descriptive_review"])
    def test_missing_fields_are_reported(self):
        result = research_coverage_scorecard([row("A", "1", sector=None)])
        self.assertEqual(result["missing_dimension_counts"]["sector"], 1)
    def test_invalid_threshold(self):
        with self.assertRaisesRegex(ValueError, "invalid_min_events"):
            research_coverage_scorecard([], min_events=0)

if __name__ == "__main__":
    unittest.main()
