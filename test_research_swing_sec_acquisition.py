import tempfile
import unittest
from unittest.mock import patch
from research_swing_sec_acquisition import download_sec_submissions

class AcquisitionSafetyTests(unittest.TestCase):
    def test_requires_contact_user_agent(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "sec_contact_user_agent_required"):
                download_sec_submissions([320193], user_agent="python", output_dir=d)
    def test_limits_company_count(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "invalid_company_count"):
                download_sec_submissions(list(range(1, 12)),
                    user_agent="Research research@example.org", output_dir=d)
    def test_rejects_duplicate_ciks(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "duplicate_cik"):
                download_sec_submissions([320193, 320193],
                    user_agent="Research research@example.org", output_dir=d)
    def test_rejects_rapid_requests(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "insufficient_request_spacing"):
                download_sec_submissions([320193],
                    user_agent="Research research@example.org",
                    output_dir=d, pause_seconds=0)
    def test_no_network_on_invalid_input(self):
        with patch("research_swing_sec_acquisition.urlopen") as request:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):
                    download_sec_submissions([], user_agent="Research research@example.org", output_dir=d)
            request.assert_not_called()

if __name__ == "__main__":
    unittest.main()
