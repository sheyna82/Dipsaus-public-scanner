"""Offline guard: direct execution of the Xetra retrieval module must not fetch."""
import runpy
import unittest
from unittest.mock import patch


class XetraCliAuthorizationTests(unittest.TestCase):
    def test_direct_module_execution_exits_before_any_network_request(self):
        with patch("urllib.request.build_opener", side_effect=AssertionError("network opener invoked")):
            with self.assertRaises(SystemExit) as caught:
                runpy.run_module(
                    "research.spoor2_xetra_artifact_retrieval_20261113",
                    run_name="__main__",
                )
        self.assertIn("explicit fresh authorization required", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
