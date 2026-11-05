"""Synthetic checks for the feature/label research join."""
import unittest
from research_daily_feature_label_join import join_features_and_labels


def sample(n):
    lines = ["date,open,high,low,close,volume"]
    for day in range(1, n + 1):
        close = 100 + day * 0.1
        lines.append(f"2026-01-{day:02d},{close},{close+1},{close-1},{close},100")
    return ("\n".join(lines) + "\n").encode()


class JoinTests(unittest.TestCase):
    def test_only_matured_labels_and_no_market_fabrication(self):
        rows = join_features_and_labels(sample(28), horizon=3)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["date"], "2026-01-20")
        self.assertEqual(rows[-1]["date"], "2026-01-25")
        self.assertTrue(all(r["market_20d_positive"] is None for r in rows))
        self.assertTrue(all(not r["point_in_time_verified"] and not r["trade_ready"]
                            for r in rows))

    def test_appending_future_day_preserves_matured_records(self):
        old = join_features_and_labels(sample(27), horizon=3)
        new = join_features_and_labels(sample(28), horizon=3)
        self.assertEqual(old, new[:len(old)])


if __name__ == "__main__":
    unittest.main()
