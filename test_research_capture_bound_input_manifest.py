import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research_capture_bound_input_manifest import audit_capture_bound_inputs, write_capture_manifest


class CaptureBoundTests(unittest.TestCase):
    def evidence(self, root, symbol):
        return {"symbol": symbol, "accepted": True, "raw_sha256": symbol.lower() * 8,
                "retrieved_at_utc": "2026-11-03T14:57:22+00:00",
                "last_conservatively_eligible_session": "2026-11-02"}

    def test_manifest_does_not_backdate_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("research_capture_bound_input_manifest.audit_yahoo_probe",
                       side_effect=self.evidence):
                report = audit_capture_bound_inputs(tmp)
                self.assertEqual(report["last_common_eligible_session"], "2026-11-02")
                self.assertEqual(report["captured_at_utc"], "2026-11-03T14:57:22+00:00")
                self.assertFalse(report["prospective_candidate_registered"])
                self.assertTrue(report["outcome_window_must_start_after_capture"])
                result = write_capture_manifest(tmp, Path(tmp) / "capture.json")
                self.assertTrue(result["sha256"])
                with self.assertRaisesRegex(ValueError, "capture_manifest_already_exists"):
                    write_capture_manifest(tmp, Path(tmp) / "capture.json")

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake(root, symbol):
                row = self.evidence(root, symbol)
                if symbol == "SPY":
                    row["accepted"] = False
                return row
            with patch("research_capture_bound_input_manifest.audit_yahoo_probe", side_effect=fake):
                with self.assertRaisesRegex(ValueError, "incomplete_capture_evidence"):
                    audit_capture_bound_inputs(tmp)


if __name__ == "__main__":
    unittest.main()
