import unittest
from research_publication_preflight import assess_public_artifact


class PublicationPreflightTests(unittest.TestCase):
    def setUp(self):
        self.observation = {
            "synthetic_data_only": True, "research_only": True,
            "trade_ready": False, "future_outcome": None,
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
        }
        self.bytes = b'{"Time Series (Daily)": {"2026-11-03": {"4. close": "102"}}}'

    def test_synthetic_fixture_may_be_uploaded(self):
        self.assertTrue(assess_public_artifact(self.observation, self.bytes)["public_upload_allowed"])

    def test_real_or_unmarked_data_denied(self):
        for flag in (False, None):
            with self.subTest(flag=flag):
                self.observation["synthetic_data_only"] = flag
                self.assertFalse(assess_public_artifact(
                    self.observation, self.bytes)["public_upload_allowed"])

    def test_secret_bytes_denied_even_if_synthetic(self):
        with self.assertRaisesRegex(ValueError, "possible_secret_in_source_bytes"):
            assess_public_artifact(self.observation, b'{"apikey":"EXAMPLE_SECRET_VALUE"}')

    def test_unsafe_proof_claims_denied(self):
        self.observation["independent_timestamp_proof"] = True
        with self.assertRaisesRegex(ValueError, "unsafe_synthetic_publication_claims"):
            assess_public_artifact(self.observation, self.bytes)


if __name__ == "__main__":
    unittest.main()
