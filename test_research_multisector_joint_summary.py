import unittest
from research_multisector_joint_summary import summarize, EXPECTED


def valid_row(symbol, sector):
    metric = {"events": 4, "mean_net_return_pct": 1.0}
    factor = {"selected": {"events": 2, "mean_net_return_pct": 2.0},
              "missed_winning_events": 1}
    return {"symbol": symbol, "sector": sector,
            "status": "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC",
            "baseline_test": metric,
            "factors": {k: factor for k in ("atr_and_structure", "atr_and_market",
                                          "atr_structure_market")}}


class JointSummaryTests(unittest.TestCase):
    def test_valid_universe(self):
        rows = [valid_row(s, sector) for s, sector in EXPECTED.items()]
        result = summarize(rows)
        self.assertEqual(result["status"], "EXPLORATORY_SECTOR_REPLICATION_SUMMARY")
        self.assertEqual(result["symbols_evaluated"], 16)
        self.assertEqual(result["comparisons"]["atr_and_structure"]["symbols_better"], 16)
        self.assertFalse(result["trade_ready"])

    def test_missing_symbol_blocks(self):
        rows = [valid_row(s, sector) for s, sector in list(EXPECTED.items())[:-1]]
        self.assertEqual(summarize(rows)["status"], "DATA_BLOCKED")

    def test_duplicate_blocks(self):
        rows = [valid_row(s, sector) for s, sector in EXPECTED.items()]
        self.assertEqual(summarize(rows + [rows[0]])["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
