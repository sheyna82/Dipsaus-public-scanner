"""Network-free verification of explicit ntfy delivery guardrails."""
import unittest
from research.spoor2_ntfy_delivery_probe_20261115 import prepare_probe, financial_test_message, TEST_BODY, TEST_TITLE


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

    def test_eighteen_character_test_topic_is_allowed(self):
        request = prepare_probe("00099446688gopevhy", enabled=True)
        self.assertEqual(request.get_method(), "POST")

    def test_blocks_obvious_production_topics(self):
        for topic in ("dipsaus_0123456789abcdefghij", "trade_0123456789abcdefghij",
                      "live_0123456789abcdefghij"):
            with self.subTest(topic=topic):
                with self.assertRaisesRegex(ValueError, "POSSIBLE_PRODUCTION_TOPIC"):
                    prepare_probe(topic, enabled=True)

    def test_calculated_financial_preview_is_synthetic_and_fail_closed(self):
        title, body = financial_test_message()
        self.assertIn("TEST BEREKEND", title)
        for expected in ("Instapzone", "Invalidatie", "Koersdoel", "R/R",
                         "Nettowinst", "69", "3454.90", "335.20",
                         "GEEN HANDELSSIGNAAL", "RESEARCH_ONLY"):
            self.assertIn(expected, body)
        request = prepare_probe(self.TOPIC, enabled=True, financial=True)
        self.assertIn("335.20", request.data.decode("utf-8"))
        self.assertEqual(request.get_method(), "POST")

    def test_constructs_only_synthetic_message(self):
        request = prepare_probe(self.TOPIC, enabled=True)
        self.assertEqual(request.full_url, "https://ntfy.sh/" + self.TOPIC)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.data.decode("utf-8"), TEST_BODY)
        self.assertIn("GEEN HANDELSSIGNAAL", TEST_TITLE)
        self.assertIn("Geen echte koers", TEST_BODY)


if __name__ == "__main__":
    unittest.main()
