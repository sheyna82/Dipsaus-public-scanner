"""Regression tests for international symbol mapping and source safety flags."""
import unittest
from research_international_universe import candidates,MARKETS

class InternationalUniverseTests(unittest.TestCase):
    def test_unique_symbols_and_market_coverage(self):
        rows=candidates()
        self.assertEqual(len(rows),128)
        self.assertEqual(len(MARKETS),23)
        self.assertEqual(len({r["symbol"] for r in rows}),len(rows))
        self.assertEqual({r["market"] for r in rows},set(MARKETS))
    def test_research_only(self):
        for r in candidates():
            self.assertFalse(r["event_timestamp_verified"])
            self.assertFalse(r["degiro_tradability_verified"])
            self.assertEqual(r["status"],"candidate_unverified")
    def test_known_symbol_mapping_requires_review(self):
        # Corporate share classes and country-specific listings need an explicit
        # exchange-reference cross-check before they are treated as valid.
        symbols={r["symbol"] for r in candidates()}
        for s in ("ROG.SW","AGL.JO","SOL.JO","NPN.JO","JMT.LS"):
            self.assertIn(s,symbols)
if __name__=="__main__":unittest.main()
