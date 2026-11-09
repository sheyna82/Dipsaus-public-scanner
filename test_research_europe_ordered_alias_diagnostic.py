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

    def test_nested_class_body_call_is_inventoried(self):
        source = ("class Outer:\n"
                  "    class Inner:\n"
                  "        result = compare()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(3, "uncertain_class_body_call")])

    def test_deep_nested_class_body_without_method_body(self):
        source = ("class Outer:\n"
                  "    class Middle:\n"
                  "        class Inner:\n"
                  "            compare()\n"
                  "            def later(self):\n"
                  "                ignored()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(4, "uncertain_class_body_call")])

    def test_nested_class_decorator_and_body_are_separate(self):
        source = ("class Outer:\n"
                  "    @decorate()\n"
                  "    class Inner:\n"
                  "        result = setup()\n")
        result = diagnose(source)
        self.assertEqual(sorted(x["line"] for x in result), [2, 4])
        self.assertTrue(all(x["classification"] == "uncertain_class_body_call"
                            for x in result))

    def test_nested_function_return_not_attributed_to_outer(self):
        source = ("def outer():\n"
                  "    def inner():\n"
                  "        return inner_call()\n"
                  "    return outer_call()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(4, "uncertain_deferred_expression_call")])

    def test_nested_function_condition_not_attributed_to_outer(self):
        source = ("def outer():\n"
                  "    async def inner():\n"
                  "        if inner_check():\n"
                  "            pass\n"
                  "    if outer_check():\n"
                  "        pass\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(5, "uncertain_deferred_expression_call")])

    def test_nested_class_method_return_not_attributed_to_outer(self):
        source = ("def outer():\n"
                  "    class Inner:\n"
                  "        def method(self):\n"
                  "            return method_call()\n"
                  "    return outer_call()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(5, "uncertain_deferred_expression_call")])


    def test_top_level_class_decorator_base_and_keyword_calls(self):
        source = ("@decorate()\n"
                  "class Outer(base_factory(), metaclass=meta_factory()):\n"
                  "    pass\n")
        result = diagnose(source)
        self.assertEqual(sorted(x["line"] for x in result), [1, 2, 2])
        self.assertTrue(all(x["classification"] == "uncertain_class_body_call"
                            and x["target"] is None for x in result))

    def test_top_level_class_header_and_body_both_inventoried(self):
        source = ("class Outer(base_factory()):\n"
                  "    value = body_call()\n")
        result = diagnose(source)
        self.assertEqual(sorted(x["line"] for x in result), [1, 2])


    def test_augmented_assignment_invalidates_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare += other\n"
                  "compare()\n")
        result = diagnose(source)
        self.assertEqual([x["classification"] for x in result],
                         ["not_proven_legacy"])

    def test_augmented_assignment_rhs_call_inventoried(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare += helper()\n"
                  "compare()\n")
        result = diagnose(source)
        self.assertEqual([(x["line"], x["classification"]) for x in result],
                         [(2, "uncertain_expression_call"),
                          (3, "not_proven_legacy")])


    def test_unrelated_import_shadows_proven_function_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "import math as compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_unrelated_from_import_shadows_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "from math import sqrt as compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_wildcard_import_invalidates_prior_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "from math import *\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_unrelated_import_then_legacy_reimport_restores_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "import math as compare\n"
                  "from research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "ordered_legacy_call")


    def test_function_definition_shadows_proven_legacy_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def compare():\n"
                  "    return None\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_async_function_definition_shadows_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "async def compare():\n"
                  "    return None\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_reimport_after_function_definition_restores_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def compare():\n"
                  "    return None\n"
                  "from research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "ordered_legacy_call")


    def test_class_definition_shadows_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class compare:\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_decorated_class_shadows_proven_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "@decorator\n"
                  "class compare:\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_reimport_after_class_definition_restores_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class compare:\n"
                  "    pass\n"
                  "from research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "ordered_legacy_call")


    def test_tuple_unpacking_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare, other = (fallback, 1)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_nested_list_unpacking_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "[other, [compare]] = [1, [fallback]]\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")

    def test_chained_assignment_unpacking_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare, other = replacement = (fallback, 1)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "not_proven_legacy")


    def test_walrus_in_call_argument_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "print((compare := fallback))\n"
                  "compare()\n")
        self.assertEqual([x["classification"] for x in diagnose(source)],
                         ["not_proven_legacy", "not_proven_legacy"])

    def test_nested_walrus_in_call_argument_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "print((other := (compare := fallback)))\n"
                  "compare()\n")
        self.assertEqual([x["classification"] for x in diagnose(source)],
                         ["not_proven_legacy", "not_proven_legacy"])


    def test_walrus_in_conditional_expression_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "(compare := fallback) if flag else other\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_walrus_in_fstring_expression_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "f'{(compare := fallback)}'\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_non_call_expression_inventories_nested_call(self):
        source = ("helper() if flag else fallback()\n")
        result = diagnose(source)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(x["classification"] == "uncertain_expression_call"
                            and x["target"] is None for x in result))


    def test_walrus_in_assignment_rhs_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "result = (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_walrus_in_nested_assignment_rhs_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "result = [x for x in [(compare := fallback)]]\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_walrus_rhs_invalidates_alias_even_when_outer_target_matches(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare = (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")


    def test_del_name_invalidates_legacy_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "del compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_del_unrelated_name_preserves_legacy_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "del unrelated\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_del_attribute_invalidates_unrelated_alias_proofs(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "del object.attr\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")


    def test_attribute_assignment_invalidates_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "obj.attr = replacement\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_subscript_assignment_invalidates_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "obj[index] = replacement\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_nested_unpacking_with_attribute_invalidates_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "other, (obj.attr, item) = replacement\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")


    def test_walrus_in_augmented_assignment_rhs_invalidates_other_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "total += (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_nested_walrus_in_augmented_assignment_rhs_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "total += (other := (compare := fallback))\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_unrelated_augmented_assignment_preserves_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "total += 1\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")


    def test_walrus_in_annotation_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "other: (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_annotation_only_does_not_rebind_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare: int\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_annotation_call_is_inventoried_as_uncertain(self):
        source = ("other: annotation_factory()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "uncertain_expression_call")


    def test_definition_decorator_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "@(decorator := (compare := fallback))\n"
                  "def later():\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_definition_default_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def later(value=(compare := fallback)):\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_unrelated_definition_preserves_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "def later(value=1):\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_class_decorator_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "@(compare := fallback)\n"
                  "class Later:\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_class_base_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later((compare := fallback)):\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_class_keyword_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later(metaclass=(compare := fallback)):\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_unrelated_class_header_preserves_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_assert_condition_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "assert (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_assert_message_walrus_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "assert False, (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_assert_message_call_inventoried_as_uncertain(self):
        source = ("assert True, helper()\n")
        self.assertEqual(diagnose(source)[0]["classification"],
                         "uncertain_expression_call")

    def test_unrelated_assert_preserves_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "assert ready\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_relative_legacy_named_import_is_not_proven(self):
        source = ("from .research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_parent_relative_legacy_named_import_is_not_proven(self):
        source = ("from ..research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_absolute_legacy_named_import_remains_proven(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_class_global_assignment_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    global compare\n"
                  "    compare = fallback\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_nested_class_global_assignment_invalidates_prior_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Outer:\n"
                  "    class Inner:\n"
                  "        global compare\n"
                  "        compare = fallback\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_class_local_assignment_preserves_module_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    compare = fallback\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_class_conditional_global_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    if enabled:\n"
                  "        global compare\n"
                  "        compare = fallback\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_class_loop_global_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    for item in items:\n"
                  "        global compare\n"
                  "        compare = item\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_method_global_does_not_imply_immediate_module_binding(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    def method(self):\n"
                  "        global compare\n"
                  "        compare = fallback\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_class_local_walrus_preserves_module_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    local = (compare := fallback)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_nested_class_header_walrus_preserves_module_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Outer:\n"
                  "    class Inner((compare := Base)):\n"
                  "        pass\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_class_method_default_walrus_preserves_module_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "class Later:\n"
                  "    def method(self, value=(compare := fallback)):\n"
                  "        return value\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_direct_exec_invalidates_prior_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "exec('compare = fallback')\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_direct_exec_with_explicit_namespace_is_conservative(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "exec(code, namespace)\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_unrelated_direct_call_preserves_prior_alias_proof(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "helper()\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "ordered_legacy_call")

    def test_exec_in_assignment_rhs_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "result = exec('compare = fallback')\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_exec_in_assert_condition_invalidates_alias(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "assert exec('compare = fallback') is None\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")

    def test_exec_in_assert_message_invalidates_alias_conservatively(self):
        source = ("from research_europe_relative_strength import compare\n"
                  "assert condition, exec('compare = fallback')\n"
                  "compare()\n")
        self.assertEqual(diagnose(source)[-1]["classification"],
                         "not_proven_legacy")


if __name__ == "__main__":
    unittest.main()
