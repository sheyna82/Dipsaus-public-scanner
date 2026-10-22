import json
import unittest
from research_multisector_source_availability import CANDIDATES, inspect_candidate


class SourceAvailabilityTests(unittest.TestCase):
    def test_declared_universe_contains_delisted(self):
        self.assertEqual(len(CANDIDATES), 12)
        self.assertIn("delisted", {row[2] for row in CANDIDATES})
        self.assertEqual(len({row[1] for row in CANDIDATES}), 11)

    def test_rejects_invalid_source(self):
        result = inspect_candidate("XOM", "Energy", "active",
                                   fetch=lambda url: b'{"chart":{"result":null}}')
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertFalse(result["trade_ready"])

    def test_does_not_claim_price_verification(self):
        result = inspect_candidate("LEH", "Financials", "delisted",
                                   fetch=lambda url: b'{}')
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["delisted_coverage_verified"])


if __name__ == "__main__":
    unittest.main()
