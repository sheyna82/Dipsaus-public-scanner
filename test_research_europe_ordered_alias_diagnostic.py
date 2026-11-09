import unittest
from research_europe_ordered_alias_diagnostic import diagnose


class OrderedAliasDiagnosticTests(unittest.TestCase):
    def test_before_and_after_rebinding(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare()\n"
                  "compare = lambda: None\n"
                  "compare()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["ordered_legacy_call", "not_proven_legacy"])

    def test_module_attribute_and_alias(self):
        source = ("import research_europe_recovery_confirmation as recovery\n"
                  "fn = recovery.evaluate\n"
                  "fn()\n"
                  "fn = None\n"
                  "fn()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["ordered_legacy_call", "not_proven_legacy"])

    def test_unrelated_function_is_not_proven_legacy(self):
        self.assertEqual(diagnose("unrelated()\n")[0]["classification"],
                         "not_proven_legacy")


if __name__ == "__main__":
    unittest.main()
