import unittest
from research_swing_broad_us_eu_universe import broad_universe_manifest,audit_broad_coverage

class BroadUniverseTests(unittest.TestCase):
    def test_regions_and_currency(self):
        m=broad_universe_manifest()
        self.assertGreaterEqual(m["region_counts"]["US"],35)
        self.assertGreaterEqual(m["region_counts"]["EU"],35)
        self.assertTrue(any(x["currency"]=="GBp" for x in m["universe"]))
        self.assertTrue(any(x["currency"]=="SEK" for x in m["universe"]))
    def test_missing_symbols_never_disappear(self):
        m=broad_universe_manifest()
        symbols=[x["symbol"] for x in m["universe"]]
        symbols += [s for group in m["benchmarks"].values() for s in group]
        statuses={s:"normalized_unverified" for s in symbols}
        statuses[symbols[0]]="unavailable"
        r=audit_broad_coverage(statuses)
        self.assertFalse(r["complete"])
        self.assertEqual(r["unavailable"],[symbols[0]])
    def test_incomplete_manifest_fails(self):
        with self.assertRaises(ValueError):
            audit_broad_coverage({})
if __name__=="__main__":
    unittest.main()
