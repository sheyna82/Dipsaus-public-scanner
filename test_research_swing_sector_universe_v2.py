import unittest
from research_swing_diversified_universe import UNIVERSE_V1
from research_swing_sector_universe_v2 import (
    EXPLORATORY_V2_ADDITIONS, expanded_universe_manifest)


class ExpandedSectorUniverseTests(unittest.TestCase):
    def test_v1_is_unchanged_and_all_eleven_sectors_balanced(self):
        manifest = expanded_universe_manifest()
        self.assertEqual(manifest["sector_count"], 11)
        self.assertEqual(manifest["symbol_count"], 22)
        self.assertEqual([(r["symbol"], r["sector"]) for r in manifest["symbols"][:18]],
                         list(UNIVERSE_V1))
        self.assertEqual([(r["symbol"], r["sector"]) for r in manifest["symbols"][18:]],
                         list(EXPLORATORY_V2_ADDITIONS))
        self.assertIs(manifest["trade_ready"], False)
        self.assertIs(manifest["source_data_validated"], False)

    def test_every_sector_has_two_symbols(self):
        from collections import Counter
        manifest = expanded_universe_manifest()
        counts = Counter(row["sector"] for row in manifest["symbols"])
        self.assertEqual(len(counts), 11)
        self.assertTrue(all(n == 2 for n in counts.values()))


if __name__ == "__main__":
    unittest.main()
