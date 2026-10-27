"""Synthetic next-open adapter timing and cost checks."""
import unittest
from datetime import date, timedelta
from decimal import Decimal
from research_swing_session_fill_adapter import proposals_from_bars


class SessionFillAdapterTests(unittest.TestCase):
    def setUp(self):
        self.bars = [{"date": date(2026, 1, 2) + timedelta(days=i),
                      "open": 100 if i < 4 else 110}
                     for i in range(7)]

    def test_signal_close_fills_next_open_and_later_exit(self):
        result = proposals_from_bars(
            {"A": self.bars}, [{"ticker": "A", "decision_index": 1,
                                "score": 3}], horizon=2,
            roundtrip_cost_bps=50)
        self.assertEqual(result[0]["decision_date"], self.bars[1]["date"])
        self.assertEqual(result[0]["entry_date"], self.bars[2]["date"])
        self.assertEqual(result[0]["exit_date"], self.bars[4]["date"])
        self.assertEqual(Decimal(result[0]["net_return_pct"]), Decimal("9.5"))

    def test_no_forward_data_fails(self):
        with self.assertRaisesRegex(ValueError, "incomplete_forward_bars"):
            proposals_from_bars(
                {"A": self.bars}, [{"ticker": "A", "decision_index": 4,
                                    "score": 1}], horizon=2)

    def test_rejects_duplicate_sessions(self):
        bars = list(self.bars)
        bars[3] = dict(bars[2])
        with self.assertRaisesRegex(ValueError, "invalid_session_calendar"):
            proposals_from_bars(
                {"A": bars}, [{"ticker": "A", "decision_index": 1,
                               "score": 1}], horizon=2)


if __name__ == "__main__":
    unittest.main()
