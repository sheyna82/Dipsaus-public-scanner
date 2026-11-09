import unittest
from research_gate_europe_legacy_calls import classify, enforce_no_unreviewed

class CallReviewTests(unittest.TestCase):
    def test_controlled_delegation_allowed(self):
        hit = {"path": "research_europe_relative_strength_admitted.py", "line": 37,
               "target": "research_europe_relative_strength.compare"}
        self.assertEqual(enforce_no_unreviewed([hit])[0]["classification"], "controlled_delegation")

    def test_historical_test_allowed(self):
        hit = {"path": "test_research_europe_recovery_confirmation.py", "line": 11,
               "target": "research_europe_recovery_confirmation.evaluate"}
        self.assertEqual(classify([hit])[0]["classification"], "historical_test")

    def test_unreviewed_script_blocks(self):
        hit = {"path": "new_research_script.py", "line": 7,
               "target": "research_europe_relative_strength.compare"}
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_LEGACY_EU_CALLS:1"):
            enforce_no_unreviewed([hit])

    def test_nested_test_name_cannot_bypass_allowlist(self):
        hit = {"path": "untrusted/test_research_europe_relative_strength.py", "line": 4,
               "target": "research_europe_relative_strength.compare"}
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_LEGACY_EU_CALLS"):
            enforce_no_unreviewed([hit])

if __name__ == "__main__":
    unittest.main()
