import unittest
from dipsaus_risk_scenario_study import study_scenario


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"high": 102, "low": 98, "close": 100}
                     for _ in range(16)]

    def test_orderly_pullback_stays_above_support(self):
        outcome = study_scenario(self.bars, 100, [101, 100, 99, 100])
        self.assertEqual([x["risk_state"] for x in outcome["observations"]],
                         ["ABOVE_REFERENCE_SUPPORT"] * 4)
        self.assertTrue(outcome["synthetic_scenario_only"])
        self.assertFalse(outcome["historically_validated"])

    def test_break_and_reclaim_remain_distinct_observations(self):
        outcome = study_scenario(self.bars, 100, [99, 97.5, 95, 99])
        self.assertEqual([x["risk_state"] for x in outcome["observations"]],
                         ["ABOVE_REFERENCE_SUPPORT", "BELOW_SUPPORT_REVIEW",
                          "DEEPER_SUPPORT_BREACH_REVIEW", "ABOVE_REFERENCE_SUPPORT"])
        self.assertFalse(outcome["automatic_sell"])
        self.assertFalse(outcome["stop_order_created"])
        self.assertTrue(all(not x["notify"] and not x["sell_recommendation"]
                            for x in outcome["observations"]))

    def test_invalid_scenarios_fail_closed(self):
        self.assertIsNone(study_scenario(self.bars, 100, []))
        self.assertIsNone(study_scenario(self.bars, 100, [99, float("nan")]))
        self.assertIsNone(study_scenario(self.bars, 100, [99], "UNVERIFIED"))


if __name__ == "__main__":
    unittest.main()
