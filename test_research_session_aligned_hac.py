"""Synthetic HAC session metadata tests."""
import unittest
from research_session_aligned_hac import evaluate_session_aligned_hac


def events():
    return [{"severe": False, "baseline_probability": 0.2,
             "atr_probability": 0.3} for _ in range(4)]


class SessionHacTests(unittest.TestCase):
    def test_flags_unverified_calendar_and_insufficient_lags(self):
        result = evaluate_session_aligned_hac(
            events(), session_dates=["2025-01-02", "2025-01-03",
                                     "2025-01-06", "2025-01-07"],
            lags=1, horizon_sessions=10)
        self.assertFalse(result["session_calendar_verified"])
        self.assertFalse(result["lags_cover_full_label_overlap"])
        self.assertFalse(result["statistical_significance_verified"])

    def test_rejects_duplicate_session(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate_session_aligned_hac(
                events(), session_dates=["2025-01-02", "2025-01-03",
                                         "2025-01-03", "2025-01-07"],
                lags=1, horizon_sessions=2)


if __name__ == "__main__":
    unittest.main()
