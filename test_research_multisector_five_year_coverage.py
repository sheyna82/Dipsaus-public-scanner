import unittest
from research_multisector_five_year_coverage import SECTORS, inspect_payload, probe

class CoverageTests(unittest.TestCase):
    def test_universe(self):
        self.assertEqual(len(SECTORS), 8)
        self.assertEqual(sum(map(len, SECTORS.values())), 16)

    def test_missing_result(self):
        result = inspect_payload("AAPL", {"chart": {"result": []}})
        self.assertEqual(result["status"], "DATA_BLOCKED")

    def test_reject_unknown_symbol(self):
        self.assertEqual(probe("INVALID")["status"], "DATA_BLOCKED")

if __name__ == "__main__":
    unittest.main()
