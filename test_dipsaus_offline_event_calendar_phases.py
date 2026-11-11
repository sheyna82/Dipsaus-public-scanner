import unittest
from datetime import date, timedelta
from dipsaus_offline_event_calendar_phases import compare_calendar_phases


def rows(n=85):
    return [{"date": (date(2026, 1, 1) + timedelta(days=i)).isoformat(), "open": 100 + i,
             "high": 101 + i, "low": 99 + i,
             "close": 100 + i, "volume": 1000} for i in range(n)]


class CalendarPhasesTests(unittest.TestCase):
    def test_phase_comparison_is_descriptive(self):
        result = compare_calendar_phases(rows())
        self.assertEqual(result["status"], "DESCRIPTIVE_PHASE_COMPARISON")
        self.assertFalse(result["predictive_edge_proven"])
        self.assertFalse(result["trade_ready"])
        self.assertGreater(result["calendar_phase_count"], 1)
        self.assertEqual(result["calendar_phase_count"], len(result["calendar_phases"]))
        self.assertTrue(result["same_number_of_entries"])
        self.assertTrue(result["nonoverlapping_entries"])
        for phase in result["calendar_phases"]:
            self.assertEqual(phase["count"], result["selected_count"])

    def test_invalid_history_is_blocked(self):
        result = compare_calendar_phases([])
        self.assertEqual(result["status"], "DATA_BLOCKED")

    def test_no_signal_is_not_comparison(self):
        flat = rows()
        for bar in flat:
            bar["open"] = bar["high"] = bar["low"] = bar["close"] = 100
        result = compare_calendar_phases(flat)
        self.assertEqual(result["status"], "INSUFFICIENT_SIGNALS")


if __name__ == "__main__":
    unittest.main()
