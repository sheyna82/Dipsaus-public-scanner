"""Offline regression: exhausted Xetra authorization must not be replayable.

This test reads workflow source files only; it never makes network requests.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ISOLATED = ROOT / ".github/workflows/spoor2-isolated-tests.yml"
EXPIRED = ROOT / ".github/workflows/spoor2-xetra-approved-once-20261118.yml"


class XetraAuthorizationExpiryTests(unittest.TestCase):
    def test_isolated_regression_keeps_offline_job(self):
        workflow = ISOLATED.read_text(encoding="utf-8")
        self.assertIn("spoor2-offline:", workflow)
        self.assertIn("python -m unittest discover", workflow)

    def test_no_reusable_network_fetch_in_either_workflow(self):
        for path in (ISOLATED, EXPIRED):
            with self.subTest(path=path.name):
                workflow = path.read_text(encoding="utf-8")
                for prohibited in (
                    "fetch_approved_second_request",
                    "approved-xetra-once:",
                    "urllib.request",
                    "urllib.error",
                    "cashmarket.deutsche-boerse.com/resource/blob/",
                ):
                    self.assertNotIn(prohibited, workflow)

    def test_expired_manual_workflow_fails_closed(self):
        workflow = EXPIRED.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("authorization-expired:", workflow)
        self.assertIn("No external requests are permitted", workflow)
        self.assertIn("exit 1", workflow)


if __name__ == "__main__":
    unittest.main()
