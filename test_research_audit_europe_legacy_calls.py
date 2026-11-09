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

if __name__ == "__main__":
    unittest.main()
