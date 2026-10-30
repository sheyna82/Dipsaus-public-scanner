import unittest
from datetime import date, timedelta
from dipsaus_offline_structure_intersection_gate import evaluate_structure_intersections


def bars(n=500, growth=0.3):
    return [{"date": (date(2024,1,1)+timedelta(days=i)).isoformat(),
             "open": 100+growth*i+(i%17)*.02,
             "high": 101+growth*i+(i%17)*.02,
             "low": 99+growth*i+(i%17)*.02,
             "close": 100+growth*i+(i%17)*.02,
             "volume": 1000} for i in range(n)]


class JointStructureTests(unittest.TestCase):
    def test_joint_counts_and_nontradable(self):
        r = evaluate_structure_intersections(bars(), bars(growth=.15), min_test=3)
        self.assertEqual(r["status"], "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC")
        for factor in r["factors"].values():
            n = (factor["selected"] or {}).get("events",0)+(factor["skipped"] or {}).get("events",0)
            self.assertEqual(n,r["test_events"])
        regimes = r["market_regime_diagnostics"]
        total = sum((v["baseline"] or {}).get("events", 0) for v in regimes.values())
        self.assertEqual(total, r["test_events"])
        for group in regimes.values():
            selected = (group["atr_structure_selected"] or {}).get("events", 0)
            rejected = (group["atr_structure_rejected"] or {}).get("events", 0)
            self.assertEqual(selected + rejected, (group["baseline"] or {}).get("events", 0))
            self.assertLessEqual(group["missed_winning_events"], rejected)
        dependence = r["dependence_diagnostic"]
        self.assertGreaterEqual(dependence["overlapping_event_pairs"], 0)
        self.assertLessEqual(dependence["greedy_nonoverlapping_event_count"], r["test_events"])
        self.assertEqual(dependence["horizon_sessions"], 10)
        self.assertFalse(dependence["independent_observations_claimed"])
        self.assertFalse(r["trade_ready"])

    def test_small_history_blocks(self):
        self.assertEqual(evaluate_structure_intersections(bars(90),bars(90,growth=.15))["status"],"DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
