import unittest
from research_prospective_signal_ledger import build_candidate


class ProspectiveLedgerTests(unittest.TestCase):
    def test_future_signal_has_no_future_label(self):
        record = build_candidate("AMD", "2026-10-26",
                                 ["100", "101", "102", "104"],
                                 ["100", "100", "100", "101"])
        self.assertTrue(record["signal_positive_past_excess"])
        self.assertIsNone(record["future_outcome"])
        self.assertFalse(record["trade_ready"])

    def test_prior_session_rejected(self):
        with self.assertRaisesRegex(ValueError, "signal_before_prospective_start"):
            build_candidate("AMD", "2026-10-23", [1, 2, 3, 4], [1, 2, 3, 4])

    def test_unknown_symbol_rejected(self):
        with self.assertRaisesRegex(ValueError, "symbol_not_preregistered"):
            build_candidate("TSLA", "2026-10-26", [1, 2, 3, 4], [1, 2, 3, 4])

    def test_invalid_close_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_close"):
            build_candidate("AMD", "2026-10-26", [1, 2, 3, 0], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
