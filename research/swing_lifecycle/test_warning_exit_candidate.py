import unittest
from datetime import date, timedelta
from research.swing_lifecycle.warning_exit_candidate import warning_exit_candidate


def bars(n=31):
    start = date(2026, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(),
             "open": 100, "high": 101, "low": 99, "close": 100}
            for i in range(n)]


class WarningExitCandidateTests(unittest.TestCase):
    def test_no_warning_keeps_baseline(self):
        result = warning_exit_candidate(bars(), ticker="TEST",
                                        entry_index=21, baseline_exit_index=29)
        self.assertEqual(result["candidate_holding_sessions"], 8)
        self.assertIsNone(result["warning_decision_date"])

    def test_warning_next_open_not_same_close(self):
        rows = bars()
        rows[24] = {"date": rows[24]["date"], "open": 94,
                    "high": 95, "low": 90, "close": 91}
        result = warning_exit_candidate(rows, ticker="TEST",
                                        entry_index=21, baseline_exit_index=29)
        self.assertEqual(result["warning_decision_date"], rows[24]["date"])
        self.assertEqual(result["candidate_exit_date"], rows[25]["date"])
        self.assertEqual(result["candidate_holding_sessions"], 4)

    def test_future_data_does_not_change_prior_exit(self):
        rows = bars()
        rows[24] = {"date": rows[24]["date"], "open": 94,
                    "high": 95, "low": 90, "close": 91}
        first = warning_exit_candidate(rows, ticker="TEST",
                                       entry_index=21, baseline_exit_index=29)
        rows[27] = {"date": rows[27]["date"], "open": 20,
                    "high": 21, "low": 19, "close": 20}
        second = warning_exit_candidate(rows, ticker="TEST",
                                        entry_index=21, baseline_exit_index=29)
        self.assertEqual(first, second)

    def test_nonchronological_dates_rejected(self):
        rows = bars()
        rows[22]["date"] = rows[21]["date"]
        with self.assertRaisesRegex(ValueError, "nonchronological_sessions"):
            warning_exit_candidate(rows, ticker="TEST",
                                   entry_index=21, baseline_exit_index=29)


if __name__ == "__main__":
    unittest.main()
