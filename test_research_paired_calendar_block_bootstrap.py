"""Synthetic tests for exploratory paired calendar-block bootstrap."""
import unittest
from research_paired_calendar_block_bootstrap import paired_calendar_block_bootstrap


def rows():
    return [
        {"event_date": f"2025-01-{day:02d}", "severe": day % 2 == 0,
         "baseline_probability": .5, "atr_probability": .5}
        for day in range(1, 9)
    ]


class CalendarBlockBootstrapTests(unittest.TestCase):
    def test_identical_forecasts_produce_zero_interval(self):
        result = paired_calendar_block_bootstrap(rows(), block_days=3,
                                                 replicates=40, seed=7)
        self.assertEqual(result["exploratory_interval"], [0, 0])
        self.assertEqual(result["exploratory_log_loss_interval"], [0, 0])
        self.assertEqual(result["observed_atr_minus_baseline_log_loss"], 0)
        self.assertEqual(result["observed_atr_minus_baseline_brier"], 0)
        self.assertFalse(result["interval_validated_for_inference"])
        self.assertFalse(result["trade_ready"])

    def test_fixed_seed_reproducible(self):
        sample = rows()
        sample[0]["atr_probability"] = .9
        a = paired_calendar_block_bootstrap(sample, block_days=3,
                                            replicates=40, seed=7)
        b = paired_calendar_block_bootstrap(sample, block_days=3,
                                            replicates=40, seed=7)
        self.assertEqual(a, b)


    def test_missing_calendar_dates_are_reported(self):
        sample = rows()
        sample.pop(3)
        result = paired_calendar_block_bootstrap(sample, block_days=2,
                                                 replicates=20, seed=1)
        self.assertTrue(result["calendar_gaps_present"])
        self.assertFalse(result["exchange_sessions_verified"])


    def test_multiple_tickers_on_same_date_stay_in_same_resampling_unit(self):
        sample = []
        for day in range(1, 9):
            for ticker in ("AAA", "BBB"):
                sample.append({
                    "ticker": ticker,
                    "event_date": f"2025-01-{day:02d}",
                    "severe": day % 2 == 0,
                    "baseline_probability": .2,
                    "atr_probability": .8,
                })
        result = paired_calendar_block_bootstrap(
            sample, block_days=3, replicates=40, seed=11)
        self.assertEqual(result["events"], 16)
        self.assertEqual(result["observed_calendar_dates"], 8)
        self.assertFalse(result["interval_validated_for_inference"])

    def test_invalid_confidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_bootstrap_settings"):
            paired_calendar_block_bootstrap(rows(), confidence="0.95")

    def test_invalid_block_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_calendar_dates"):
            paired_calendar_block_bootstrap(rows(), block_days=20)


if __name__ == "__main__":
    unittest.main()
