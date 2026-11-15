"""Network-free verification of explicit ntfy delivery guardrails."""
import unittest
from research.spoor2_ntfy_delivery_probe_20261115 import prepare_probe, TEST_BODY, TEST_TITLE


class NtfyDeliveryProbeTests(unittest.TestCase):
    TOPIC = "testonly_0123456789abcdefghij"

    def test_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(ValueError, "EXPLICIT_TEST_OPT_IN_REQUIRED"):
            prepare_probe(self.TOPIC)

    def test_rejects_short_or_invalid_topic(self):
        for topic in ("short", "a/b", "", "https://ntfy.sh/a", "a" * 101):
            with self.subTest(topic=topic):
                with self.assertRaises(ValueError):
                    prepare_probe(topic, enabled=True)

    def test_blocks_obvious_production_topics(self):
        for topic in ("dipsaus_0123456789abcdefghij", "trade_0123456789abcdefghij",
                      "live_0123456789abcdefghij"):
            with self.subTest(topic=topic):
                with self.assertRaisesRegex(ValueError, "POSSIBLE_PRODUCTION_TOPIC"):
                    prepare_probe(topic, enabled=True)

    def test_constructs_only_synthetic_message(self):
        request = prepare_probe(self.TOPIC, enabled=True)
        self.assertEqual(request.full_url, "https://ntfy.sh/" + self.TOPIC)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.data.decode("utf-8"), TEST_BODY)
        self.assertIn("GEEN HANDELSSIGNAAL", TEST_TITLE)
        self.assertIn("Geen echte koers", TEST_BODY)


if __name__ == "__main__":
    unittest.main()
