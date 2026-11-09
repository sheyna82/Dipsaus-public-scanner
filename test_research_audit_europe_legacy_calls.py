import pathlib
import tempfile
import unittest
from research_audit_europe_legacy_calls import inventory

class LegacyCallAuditTests(unittest.TestCase):
    def test_detects_direct_and_aliased_legacy_calls(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "sample.py"
            file.write_text(
                "from research_europe_relative_strength import compare as legacy_compare\n"
                "import research_europe_recovery_confirmation as recovery\n"
                "legacy_compare({}, {}, {}, '2026-11-06')\n"
                "recovery.evaluate([], '2026-11-06', True)\n",
                encoding="utf-8")
            found = inventory([file])
            self.assertEqual([hit["line"] for hit in found], [3, 4])
            self.assertEqual({hit["target"] for hit in found}, {
                "research_europe_relative_strength.compare",
                "research_europe_recovery_confirmation.evaluate"})

    def test_ignores_mentions_without_calls(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "sample.py"
            file.write_text("from research_europe_relative_strength import compare\n"
                            "description = 'compare()'\n", encoding="utf-8")
            self.assertEqual(inventory([file]), [])

    def test_unparsable_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "broken.py"
            file.write_text("def broken(\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "UNPARSABLE_PYTHON_SOURCE"):
                inventory([file])

    def test_dynamic_legacy_import_is_flagged(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "dynamic.py"
            file.write_text("import importlib\n"
                            "module = importlib.import_module('research_europe_relative_strength')\n",
                            encoding="utf-8")
            found = inventory([file])
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["kind"], "dynamic_import")

    def test_computed_import_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "computed.py"
            file.write_text("name = 'research_europe_recovery_confirmation'\n"
                            "module = __import__(name)\n", encoding="utf-8")
            found = inventory([file])
            self.assertEqual(found[0]["target"], "unknown_dynamic_import")

    def test_getattr_legacy_function_is_flagged(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "reflect.py"
            file.write_text("import research_europe_relative_strength as legacy\n"
                            "fn = getattr(legacy, 'compare')\n", encoding="utf-8")
            found = inventory([file])
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["kind"], "reflective_access")

    def test_computed_getattr_is_flagged(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "reflect.py"
            file.write_text("import research_europe_recovery_confirmation as legacy\n"
                            "fn = getattr(legacy, method)\n", encoding="utf-8")
            self.assertEqual(inventory([file])[0]["target"], "unknown_reflective_access")

    def test_exec_with_legacy_module_is_flagged(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "dynamic.py"
            file.write_text("exec('import research_europe_relative_strength')\n", encoding="utf-8")
            self.assertEqual(inventory([file])[0]["kind"], "dynamic_code")

    def test_assignment_alias_of_imported_function_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "alias.py"
            file.write_text("from research_europe_relative_strength import compare\n"
                            "first = compare\n"
                            "second = first\n"
                            "second({}, {}, {}, '2026-11-06')\n", encoding="utf-8")
            found = inventory([file])
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["target"], "research_europe_relative_strength.compare")

    def test_assignment_alias_of_module_attribute_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "alias.py"
            file.write_text("import research_europe_recovery_confirmation as module\n"
                            "fn = module.evaluate\n"
                            "fn([], '2026-11-06')\n", encoding="utf-8")
            found = inventory([file])
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["target"], "research_europe_recovery_confirmation.evaluate")

    def test_legacy_alias_rebinding_is_marked_ambiguous(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "rebind.py"
            file.write_text("from research_europe_relative_strength import compare\n"
                            "fn = compare\n"
                            "fn = lambda *args: None\n"
                            "fn()\n", encoding="utf-8")
            found = inventory([file])
            self.assertTrue(any(x.get("kind") == "ambiguous_alias" for x in found))

    def test_local_parameter_shadowing_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "scope.py"
            file.write_text("from research_europe_relative_strength import compare\n"
                            "def run(compare):\n"
                            "    return compare()\n", encoding="utf-8")
            self.assertTrue(any(x.get("kind") == "ambiguous_scope"
                                for x in inventory([file])))

    def test_local_assignment_shadowing_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as root:
            file = pathlib.Path(root) / "scope.py"
            file.write_text("import research_europe_recovery_confirmation as legacy\n"
                            "def run():\n"
                            "    legacy = object()\n"
                            "    return legacy.evaluate()\n", encoding="utf-8")
            self.assertTrue(any(x.get("kind") == "ambiguous_scope"
                                for x in inventory([file])))

if __name__ == "__main__":
    unittest.main()
