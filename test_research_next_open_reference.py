import unittest
from research_next_open_reference import assess_next_open_reference


class EntryReferenceTests(unittest.TestCase):
    def bar(self, symbol, session="2026-11-04", verified=True):
        return {"symbol": symbol, "session": session, "open": "100.50",
                "retrieved_at_utc": "2026-11-04T21:00:00+00:00",
                "source_verified_independently": verified}

    def test_eligible_but_not_execution_proof(self):
        x = assess_next_open_reference(registered_at_utc="2026-11-03T15:00:00+00:00",
            stock_bar=self.bar("AMD"), benchmark_bar=self.bar("SPY"))
        self.assertTrue(x["entry_reference_accepted"])
        self.assertFalse(x["execution_price_verified"])

    def test_same_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "entry_not_after_registration_day"):
            assess_next_open_reference(registered_at_utc="2026-11-03T15:00:00+00:00",
                stock_bar=self.bar("AMD", "2026-11-03"),
                benchmark_bar=self.bar("SPY", "2026-11-03"))

    def test_unverified_vendor_is_not_eligible(self):
        x = assess_next_open_reference(registered_at_utc="2026-11-03T15:00:00+00:00",
            stock_bar=self.bar("AMD", verified=False), benchmark_bar=self.bar("SPY"))
        self.assertFalse(x["entry_reference_accepted"])

    def test_misaligned_sessions_rejected(self):
        with self.assertRaisesRegex(ValueError, "entry_sessions_not_aligned"):
            assess_next_open_reference(registered_at_utc="2026-11-03T15:00:00+00:00",
                stock_bar=self.bar("AMD"), benchmark_bar=self.bar("SPY", "2026-11-05"))


if __name__ == "__main__":
    unittest.main()
