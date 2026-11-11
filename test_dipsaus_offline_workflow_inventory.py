import tempfile
import unittest
from pathlib import Path
from dipsaus_offline_workflow_inventory import audit_workflows, WORKFLOWS


class WorkflowInventoryTests(unittest.TestCase):
    def test_missing_files_remain_unknown(self):
        with tempfile.TemporaryDirectory() as root:
            report = audit_workflows(root)
        self.assertTrue(all(x["status"] == "UNKNOWN"
                            for x in report["workflows"].values()))
        self.assertFalse(report["delivery_confirmed"])

    def test_static_configuration_does_not_claim_delivery(self):
        with tempfile.TemporaryDirectory() as root:
            for rel in WORKFLOWS.values():
                path = Path(root) / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("concurrency: x\ntimeout-minutes: 10\n"
                                "SCANNER_NOTIFICATIONS_ENABLED: 'false'\n"
                                "  - cron: '*/5 * * * *'\n")
            report = audit_workflows(root)
        self.assertTrue(all(x["status"] == "CONFIG_OBSERVED"
                            for x in report["workflows"].values()))
        self.assertFalse(report["delivery_confirmed"])
        self.assertFalse(report["trade_ready"])


if __name__ == "__main__":
    unittest.main()
