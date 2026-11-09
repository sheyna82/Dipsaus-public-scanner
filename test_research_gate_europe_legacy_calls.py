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

    def test_dynamic_import_not_allowlisted_even_inside_wrapper(self):
        hit = {"path": "research_europe_relative_strength_admitted.py", "line": 4,
               "target": "research_europe_relative_strength.compare",
               "kind": "dynamic_import"}
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_LEGACY_EU_CALLS"):
            enforce_no_unreviewed([hit])

    def test_reflective_access_cannot_use_wrapper_allowlist(self):
        hit = {"path": "research_europe_relative_strength_admitted.py", "line": 7,
               "target": "research_europe_relative_strength.compare",
               "kind": "reflective_access"}
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_LEGACY_EU_CALLS"):
            enforce_no_unreviewed([hit])

    def test_dynamic_code_is_not_allowlisted(self):
        hit = {"path": "test_research_europe_relative_strength.py", "line": 7,
               "target": "legacy_dynamic_code", "kind": "dynamic_code"}
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_LEGACY_EU_CALLS"):
            enforce_no_unreviewed([hit])

if __name__ == "__main__":
    unittest.main()
