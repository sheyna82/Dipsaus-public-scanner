"""Regression checks for consecutive-close warning confirmation (research only)."""
import unittest
from unittest.mock import patch

from research.swing_lifecycle.warning_exit_candidate import warning_exit_candidate


def bars():
    from datetime import date, timedelta
    start = date(2025, 1, 1)
    return [
        {"date": (start + timedelta(days=i)).isoformat(),
         "open": 100., "high": 101., "low": 99., "close": 100.}
        for i in range(40)
    ]


class ConfirmationTests(unittest.TestCase):
    def test_consecutive_warning_confirmation(self):
        series = bars()
        def signal(_rows, t, **kwargs):
            return {"warning": t in (23, 25, 26)}
        with patch("research.swing_lifecycle.warning_exit_candidate.failure_warning_at_close", side_effect=signal):
            one = warning_exit_candidate(series, ticker="TEST", entry_index=21,
                                         baseline_exit_index=32, confirmation_sessions=1)
            two = warning_exit_candidate(series, ticker="TEST", entry_index=21,
                                         baseline_exit_index=32, confirmation_sessions=2)
            three = warning_exit_candidate(series, ticker="TEST", entry_index=21,
                                           baseline_exit_index=32, confirmation_sessions=3)
        self.assertEqual(one["candidate_exit_date"], series[24]["date"])
        self.assertEqual(two["candidate_exit_date"], series[27]["date"])
        self.assertEqual(three["candidate_exit_date"], series[32]["date"])

    def test_invalid_confirmation_fails_closed(self):
        for value in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                warning_exit_candidate(bars(), ticker="TEST", entry_index=21,
                                       baseline_exit_index=32, confirmation_sessions=value)


if __name__ == "__main__":
    unittest.main()
