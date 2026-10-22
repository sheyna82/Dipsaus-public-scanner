import unittest
from datetime import date, timedelta
from dipsaus_offline_event_history_outcomes import evaluate_daily_event_history


def bars(count=75, direction=1):
    rows = []
    day = date(2026, 1, 1)
    for i in range(count):
        price = 100 + direction * i * 0.2
        rows.append({"date": day.isoformat(), "open": price, "high": price + 1,
                     "low": price - 1, "close": price, "volume": 1000})
        day += timedelta(days=1)
    return rows


class EventHistoryOutcomesTests(unittest.TestCase):
    def test_rising_history_has_nonoverlap(self):
        result = evaluate_daily_event_history(bars())
        self.assertEqual(result["status"], "DESCRIPTIVE_HISTORY")
        self.assertGreater(result["sample_count"], 0)
        self.assertTrue(result["sample_count"] <= 5)
        self.assertFalse(result["predictive_edge_proven"])

    def test_declining_history_no_entries(self):
        result = evaluate_daily_event_history(bars(direction=-1))
        self.assertEqual(result["sample_count"], 0)
        self.assertIsNone(result["mean_terminal_net_pct"])

    def test_invalid_horizon_blocks(self):
        self.assertEqual(evaluate_daily_event_history(bars(), horizon=0)["status"],
                         "DATA_BLOCKED")

    def test_invalid_fee_blocks(self):
        self.assertEqual(evaluate_daily_event_history(bars(), fee_bps_each_side=-1)["status"],
                         "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
