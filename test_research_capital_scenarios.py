import unittest
from research_capital_scenarios import compare_capital_scenarios

def scenario(**overrides):
    kwargs = {"budget_eur": 50000, "invested_eur": 2000,
              "free_room_eur": 48000, "observed_positions": 2}
    kwargs.update(overrides)
    return compare_capital_scenarios(**kwargs)

class CapitalScenarioTests(unittest.TestCase):
    def test_four_slots_and_no_authorization(self):
        report = scenario()
        self.assertEqual(report["illustrative_unfilled_slots"], 4)
        self.assertEqual(report["scenarios"][0]["illustrative_new_allocation_eur"], 14000)
        self.assertFalse(report["trade_ready"])
        self.assertIsNone(report["allocation_recommendation"])
        self.assertFalse(report["cash_authenticated"])

    def test_large_tranche_cannot_override_budget(self):
        report = scenario(budget_eur=20000, free_room_eur=50000)
        large = report["scenarios"][-1]
        self.assertFalse(large["within_budget_if_existing_positions_unchanged"])
        self.assertTrue(large["within_displayed_free_room_only"])
        self.assertFalse(large["trade_ready"])

    def test_full_portfolio_has_no_new_slots(self):
        report = scenario(observed_positions=6)
        self.assertEqual(report["illustrative_unfilled_slots"], 0)
        self.assertTrue(all(s["illustrative_new_allocation_eur"] == 0 for s in report["scenarios"]))

    def test_over_capacity_never_produces_negative_slots(self):
        self.assertEqual(scenario(observed_positions=8)["illustrative_unfilled_slots"], 0)

    def test_invalid_capital_inputs_fail_closed(self):
        for invalid in (True, -1, float("nan"), float("inf"), None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    scenario(free_room_eur=invalid)

    def test_invalid_tranche_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRANCHE_SIZES"):
            scenario(tranche_sizes=[3500, 0])

if __name__ == "__main__":
    unittest.main()
