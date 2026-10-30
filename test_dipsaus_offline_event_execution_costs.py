import unittest
from datetime import date, timedelta
from dipsaus_offline_event_execution_costs import compare_execution_costs


class ExecutionCostTests(unittest.TestCase):
    def test_rejects_missing_history(self):
        self.assertEqual(compare_execution_costs([])["status"], "DATA_BLOCKED")

    def test_rejects_invalid_cost(self):
        self.assertEqual(compare_execution_costs([], cost_bps_each_side=(10, -1))["reason"],
                         "INVALID_COST_SCENARIOS")

    def test_cost_sensitivity_preserves_signal_set(self):
        rows = []
        for i in range(70):
            p = 100 + i
            rows.append({"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                         "open": p, "high": p + 1, "low": p - 1,
                         "close": p + .5, "volume": 10000})
        result = compare_execution_costs(rows)
        self.assertEqual(result["status"], "DESCRIPTIVE_COST_SENSITIVITY")
        self.assertGreater(result["scenarios"][0]["signal_count"], 0)
        self.assertEqual(len({x["signal_count"] for x in result["scenarios"]}), 1)
        means = [x["mean_terminal_net_pct"] for x in result["scenarios"]]
        self.assertGreater(means[0], means[1])
        self.assertGreater(means[1], means[2])


if __name__ == "__main__":
    unittest.main()
