import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from candidate_coverage_runtime_gate import check_hydrated_runtime

NOW = datetime(2026, 10, 20, 15, tzinfo=timezone.utc)
class RuntimeGateTests(unittest.TestCase):
    def test_real_file_shapes_without_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"config").mkdir(); (root/"reports").mkdir()
            (root/"config/manual_recovery_triggers.json").write_text(json.dumps(
                {"candidates":{"SYNTHETIC_A":{}, "SYNTHETIC_B":{}}}))
            (root/"reports/manual_recovery_trigger_report.json").write_text(json.dumps(
                {"generated_utc":NOW.isoformat(),"rows":[
                    {"symbol":"SYNTHETIC_A","status":"WATCH","provider_freshness_pass":True}]}))
            result=check_hydrated_runtime(root/"config",root/"reports",now=NOW)
            self.assertEqual(result["active"],2)
            self.assertEqual(result["overdue"],1)
            self.assertFalse(result["reconciled"])
            self.assertNotIn("SYNTHETIC_A",str(result))
    def test_old_report_not_freshened_by_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"config").mkdir(); (root/"reports").mkdir()
            (root/"config/manual_recovery_triggers.json").write_text(json.dumps(
                {"candidates":{"SYNTHETIC_A":{}}}))
            (root/"reports/manual_recovery_trigger_report.json").write_text(json.dumps(
                {"generated_utc":"2026-10-20T14:00:00+00:00","rows":[
                    {"symbol":"SYNTHETIC_A","status":"WATCH","provider_freshness_pass":True}]}))
            result=check_hydrated_runtime(root/"config",root/"reports",now=NOW)
            self.assertEqual(result["overdue"],1)
if __name__=="__main__":
    unittest.main()
