import unittest
from research_source_secret_screen import reject_obvious_secrets


class SecretScreenTests(unittest.TestCase):
    def test_rejects_common_credentials(self):
        samples = (
            b'{"apikey":"EXAMPLE_SECRET_VALUE"}',
            b'{"access_token":"EXAMPLE_SECRET_VALUE"}',
            b'Authorization: Bearer exampletokenvalue123',
            b'client_secret=EXAMPLE_SECRET_VALUE',
        )
        for sample in samples:
            with self.subTest(sample=sample[:10]), self.assertRaisesRegex(
                    ValueError, "possible_secret_in_source_bytes"):
                reject_obvious_secrets(sample)

    def test_normal_market_data_passes_without_claiming_safety(self):
        result = reject_obvious_secrets(b'{"Time Series (Daily)":{"2026-11-03":{"4. close":"102"}}}')
        self.assertFalse(result["secret_free_proven"])
        self.assertFalse(result["safe_to_publish_proven"])


if __name__ == "__main__":
    unittest.main()
