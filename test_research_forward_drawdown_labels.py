"""Synthetic regression tests for forward drawdown outcome labels."""
import unittest
from research_forward_drawdown_labels import label_forward_drawdown


def csv_data(closes):
    lines = ["date,open,high,low,close,volume"]
    for i, close in enumerate(closes, 1):
        lines.append(f"2026-01-{i:02d},{close},{close+1},{close-1},{close},100")
    return ("\n".join(lines) + "\n").encode()


class ForwardDrawdownTests(unittest.TestCase):
    def test_decline_and_censored_tail(self):
        rows = label_forward_drawdown(csv_data([100, 99, 90, 95, 96]), horizon=2)
        self.assertEqual([r["severe"] for r in rows], [True, True, False])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["label_available_date"], "2026-01-03")
        self.assertTrue(all(not r["trade_ready"] for r in rows))

    def test_future_extension_does_not_change_matured_labels(self):
        old = label_forward_drawdown(csv_data([100, 99, 90, 95]), horizon=2)
        new = label_forward_drawdown(csv_data([100, 99, 90, 95, 110]), horizon=2)
        self.assertEqual(old, new[:len(old)])

    def test_invalid_parameters(self):
        for kwargs in ({"horizon": 0}, {"horizon": True},
                       {"threshold": 0}, {"threshold": 1},
                       {"threshold": float("nan")}):
            with self.assertRaises(ValueError):
                label_forward_drawdown(csv_data([100, 99, 90]), **kwargs)


if __name__ == "__main__":
    unittest.main()
