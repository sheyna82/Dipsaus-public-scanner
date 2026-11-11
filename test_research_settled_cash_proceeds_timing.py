import unittest
from research_settled_cash import simulate_settled_cash

class ProceedsTimingTests(unittest.TestCase):
    def test_future_exit_not_mislabeled_as_already_exited(self):
        candidates = [{"id": "a", "symbol": "AMD", "entry_date": "2026-10-01",
                       "exit_date": "2026-10-15", "realized_return_pct": 2},
                      {"id": "b", "symbol": "META", "entry_date": "2026-10-02",
                       "exit_date": "2026-10-16", "realized_return_pct": 1}]
        r = simulate_settled_cash(candidates, starting_settled_cash_eur=10000,
                                  tranche_eur=3500, require_symbol=True)
        self.assertEqual(r["asof_last_entry_date"], "2026-10-02")
        self.assertEqual(r["exited_but_unsettled_proceeds_eur"], 0)
        self.assertGreater(r["future_not_yet_exited_proceeds_eur"], 0)
        self.assertAlmostEqual(r["unsettled_proceeds_eur"],
                               r["future_not_yet_exited_proceeds_eur"])

    def test_exited_unsettled_separate_from_future_exits(self):
        candidates = [{"id": "a", "symbol": "AMD", "entry_date": "2026-10-01",
                       "exit_date": "2026-10-03", "realized_return_pct": 2},
                      {"id": "b", "symbol": "META", "entry_date": "2026-10-04",
                       "exit_date": "2026-10-16", "realized_return_pct": 1}]
        r = simulate_settled_cash(candidates, starting_settled_cash_eur=10000,
                                  tranche_eur=3500, settlement_calendar_days=2,
                                  require_symbol=True)
        self.assertGreater(r["exited_but_unsettled_proceeds_eur"], 0)
        self.assertGreater(r["future_not_yet_exited_proceeds_eur"], 0)
        self.assertAlmostEqual(r["unsettled_proceeds_eur"],
                               r["exited_but_unsettled_proceeds_eur"] +
                               r["future_not_yet_exited_proceeds_eur"])

if __name__ == "__main__":
    unittest.main()
