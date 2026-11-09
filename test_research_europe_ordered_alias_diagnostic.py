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


    def test_if_else_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "if condition:\n"
                  "    compare = lambda: None\n"
                  "else:\n"
                  "    pass\n"
                  "compare()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_control_flow", "not_proven_legacy"])

    def test_loop_invalidates_prior_alias(self):
        source = ("import research_europe_recovery_confirmation as recovery\n"
                  "for item in items:\n"
                  "    recovery = item\n"
                  "recovery.evaluate()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_control_flow", "not_proven_legacy"])

    def test_reimport_after_branch_restores_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "while condition:\n"
                  "    compare = None\n"
                  "from research_europe_relative_strength import compare\n"
                  "compare()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_control_flow", "ordered_legacy_call"])

    def test_nested_branch_call_is_reported_without_target_claim(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "if condition:\n"
                  "    compare()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_control_flow", "uncertain_nested_call"])
        self.assertIsNone(result[1]["target"])
        self.assertEqual(result[1]["line"], 3)

    def test_nested_loop_call_is_reported_without_target_claim(self):
        source = ("import research_europe_recovery_confirmation as recovery\n"
                  "for item in items:\n"
                  "    recovery.evaluate()\n")
        result = diagnose(source)
        self.assertTrue(any(x["classification"] == "uncertain_nested_call"
                            and x["line"] == 3 for x in result))

    def test_function_definition_inside_branch_is_not_traversed(self):
        source = ("if condition:\n"
                  "    def later():\n"
                  "        unrelated()\n")
        result = diagnose(source)
        self.assertFalse(any(x["classification"] == "uncertain_nested_call"
                             for x in result))

    def test_assignment_rhs_call_is_inventoried(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "value = compare()\n")
        result = diagnose(source)
        self.assertEqual(result[0]["classification"], "uncertain_expression_call")
        self.assertEqual(result[0]["line"], 2)
        self.assertIsNone(result[0]["target"])

    def test_nested_argument_call_is_inventoried(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "print(compare())\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_expression_call", "not_proven_legacy"])

    def test_outer_legacy_call_with_nested_argument(self):
        source = ("from research_europe_recovery_confirmation import evaluate\n"
                  "evaluate(helper())\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_expression_call", "ordered_legacy_call"])

    def test_return_expression_call_is_deferred(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def later():\n"
                  "    return compare()\n")
        result = diagnose(source)
        self.assertEqual(result[0]["classification"],
                         "uncertain_deferred_expression_call")
        self.assertEqual(result[0]["line"], 3)

    def test_function_condition_call_is_deferred(self):
        source = ("def later():\n"
                  "    if check():\n"
                  "        pass\n")
        result = diagnose(source)
        self.assertEqual(result[0]["classification"],
                         "uncertain_deferred_expression_call")
        self.assertEqual(result[0]["line"], 2)

    def test_assert_condition_call_is_uncertain(self):
        result = diagnose("assert check()\n")
        self.assertEqual(result[0]["classification"],
                         "uncertain_expression_call")
        self.assertEqual(result[0]["line"], 1)

    def test_default_argument_runs_at_definition_not_invocation(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def later(value=compare()):\n"
                  "    return value\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_definition_time_call")])

    def test_decorator_call_is_definition_time(self):
        source = ("@factory()\n"
                  "def later():\n"
                  "    return 1\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(1, "uncertain_definition_time_call")])

    def test_return_body_stays_deferred_while_default_is_immediate(self):
        source = ("def later(value=setup()):\n"
                  "    return process()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["uncertain_definition_time_call",
                          "uncertain_deferred_expression_call"])

    def test_function_body_expression_is_deferred(self):
        result = diagnose("def later():\n    compare()\n")
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_deferred_body_call")])

    def test_class_body_expression_is_creation_time(self):
        result = diagnose("class Research:\n    compare()\n")
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_class_body_call")])

    def test_class_assignment_call_is_creation_time_not_method_body(self):
        source = ("class Research:\n"
                  "    result = compare()\n"
                  "    def later(self):\n"
                  "        compare()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_class_body_call")])

    def test_method_decorator_is_class_creation_time(self):
        source = ("class Research:\n"
                  "    @decorator()\n"
                  "    def later(self):\n"
                  "        pass\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_class_body_call")])

    def test_method_default_is_class_creation_time(self):
        source = ("class Research:\n"
                  "    def later(self, value=setup()):\n"
                  "        pass\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_class_body_call")])

    def test_nested_class_base_and_decorator_are_visible(self):
        source = ("class Outer:\n"
                  "    @decorate()\n"
                  "    class Inner(base_factory()):\n"
                  "        pass\n")
        result = diagnose(source)
        self.assertEqual(sorted(x["line"] for x in result), [2, 3])
        self.assertTrue(all(x["classification"] == "uncertain_class_body_call"
                            for x in result))

if __name__ == "__main__":
    unittest.main()
