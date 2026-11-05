import unittest
from research_tranche_capacity_comparison import compare_tranche_capacity

class TrancheProceedsTimingTests(unittest.TestCase):
    def test_comparison_exposes_future_and_exited_proceeds_separately(self):
        candidates = [
            {"id": "a", "symbol": "AMD", "entry_date": "2026-10-01",
             "exit_date": "2026-10-05", "realized_return_pct": 2},
            {"id": "b", "symbol": "META", "entry_date": "2026-10-06",
             "exit_date": "2026-10-16", "realized_return_pct": 1},
        ]
        result = compare_tranche_capacity(candidates,
                    starting_settled_cash_eur=10000, tranches_eur=(3500,))
        scenario = result["scenarios"][0]
        self.assertEqual(scenario["asof_last_entry_date"], "2026-10-06")
        self.assertTrue(scenario["unsettled_proceeds_includes_future_exits"])
        self.assertGreater(scenario["future_not_yet_exited_proceeds_eur"], 0)
        self.assertGreater(scenario["exited_but_unsettled_proceeds_eur"], 0)
        self.assertAlmostEqual(scenario["unsettled_proceeds_eur"],
            scenario["future_not_yet_exited_proceeds_eur"] +
            scenario["exited_but_unsettled_proceeds_eur"])

if __name__ == "__main__":
    unittest.main()
