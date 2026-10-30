import unittest
from research_prospective_batch import generate_prospective_batch


class ProspectiveBatchTests(unittest.TestCase):
    def setUp(self):
        self.days = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-26"]
        self.spy = [{"date": day, "close": 100 + i} for i, day in enumerate(self.days)]
        self.stock = {symbol: [{"date": day, "close": 100 + 2 * i}
                      for i, day in enumerate(self.days)]
                      for symbol in ("COHU", "AMD", "META")}

    def test_complete_batch(self):
        result = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        self.assertEqual([r["status"] for r in result["results"]], ["candidate"] * 3)
        self.assertEqual(result["results"][0]["record"]["input_sessions"], self.days)
        self.assertFalse(result["trade_ready"])

    def test_missing_session_is_not_filled(self):
        self.stock["AMD"].pop(1)
        result = generate_prospective_batch(self.stock, self.spy,
                                            signal_session="2026-10-26")
        self.assertEqual(result["results"][1]["status"], "missing_stock_trading_session")

    def test_duplicate_session_rejected(self):
        self.spy.append(self.spy[-1].copy())
        with self.assertRaisesRegex(ValueError, "duplicate_spy_session"):
            generate_prospective_batch(self.stock, self.spy,
                                       signal_session="2026-10-26")


if __name__ == "__main__":
    unittest.main()
