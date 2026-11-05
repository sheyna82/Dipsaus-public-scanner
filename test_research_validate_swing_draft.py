"""Tests for inactive prospective swing protocol draft."""
import json
import tempfile
import unittest
from pathlib import Path
from research_validate_swing_draft import validate_swing_draft


class SwingDraftTests(unittest.TestCase):
    def test_draft_is_valid_but_inactive(self):
        result = validate_swing_draft()
        self.assertTrue(result["valid_draft"])
        self.assertFalse(result["active"])
        self.assertGreater(result["unresolved_count"], 0)

    def test_activation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path("research/prospective_swing_protocol_v0_draft.json")
            data = json.loads(source.read_text())
            data["status"] = "ACTIVE"
            path = Path(tmp) / "draft.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "inactive"):
                validate_swing_draft(path)

    def test_auto_orders_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path("research/prospective_swing_protocol_v0_draft.json")
            data = json.loads(source.read_text())
            data["entry_decision"]["orders"] = "AUTO"
            path = Path(tmp) / "draft.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "orders_must_be_disabled"):
                validate_swing_draft(path)


if __name__ == "__main__":
    unittest.main()
