"""Causal ATR feature extractor regression tests, synthetic only."""
import unittest
from research_daily_atr_feature_extractor import extract_daily_structure


def sample(n=25):
    lines = ["date,open,high,low,close,volume"]
    for day in range(1, n + 1):
        close = 10 + day * .1
        lines.append(f"2026-01-{day:02d},{close},{close + 1},{close - 1},{close},100")
    return ("\n".join(lines) + "\n").encode()


class FeatureExtractorTests(unittest.TestCase):
    def test_extracts_without_future_labels(self):
        features = extract_daily_structure(sample())
        self.assertEqual(len(features), 6)
        self.assertTrue(all(row["severe"] is None and row["market_20d_positive"] is None
                            and not row["trade_ready"] for row in features))

    def test_appending_future_bar_does_not_change_past_features(self):
        old = extract_daily_structure(sample(24))
        new = extract_daily_structure(sample(25))
        self.assertEqual(old, new[:len(old)])

    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            extract_daily_structure(sample(), atr_window=1)


if __name__ == "__main__":
    unittest.main()
