"""Coordinated historical eligibility regression tests."""

import unittest

from research_historical_eligibility_gate import assess_historical_revision

ORIGINAL = {
    "revision_id": "original",
    "observed_at": "2026-01-01T09:00:00+00:00",
    "published_at": "2026-01-01T10:00:00+00:00",
    "ingested_at": "2026-01-01T11:00:00+00:00",
    "revision_asof": "2026-01-01T10:00:00+00:00",
}
REVISED = {
    **ORIGINAL,
    "revision_id": "revised",
    "published_at": "2026-01-06T10:00:00+00:00",
    "ingested_at": "2026-01-06T11:00:00+00:00",
    "revision_asof": "2026-01-06T10:00:00+00:00",
}


class HistoricalEligibilityTests(unittest.TestCase):
    def test_original_selected_before_revision(self):
        result = assess_historical_revision(
            [REVISED, ORIGINAL], decision_at="2026-01-05T12:00:00+00:00")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["revision_id"], "original")
        self.assertFalse(result["trade_ready"])

    def test_revision_selected_after_publication(self):
        result = assess_historical_revision(
            [ORIGINAL, REVISED], decision_at="2026-01-07T12:00:00+00:00")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["revision_id"], "revised")

    def test_missing_revision_timestamp_rejected(self):
        bad = {**ORIGINAL}
        bad.pop("revision_asof")
        result = assess_historical_revision(
            [bad], decision_at="2026-01-05T12:00:00+00:00")
        self.assertFalse(result["accepted"])
        self.assertIn("invalid_revision_asof", result["reasons"])

    def test_no_available_revision_rejected(self):
        result = assess_historical_revision(
            [REVISED], decision_at="2026-01-05T12:00:00+00:00")
        self.assertFalse(result["accepted"])
        self.assertIn("future_published_at", result["reasons"])

    def test_invalid_newer_version_does_not_hide_valid_original(self):
        malformed = {**REVISED, "revision_asof": "not-a-timestamp"}
        result = assess_historical_revision(
            [ORIGINAL, malformed], decision_at="2026-01-07T12:00:00+00:00")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["revision_id"], "original")

    def test_duplicate_revision_id_rejected_even_if_one_invalid(self):
        malformed = {**ORIGINAL, "revision_asof": "invalid"}
        with self.assertRaisesRegex(ValueError, "duplicate_revision_id"):
            assess_historical_revision(
                [ORIGINAL, malformed], decision_at="2026-01-05T12:00:00+00:00")

    def test_generator_input_rejected_explicitly(self):
        versions = (version for version in [ORIGINAL])
        with self.assertRaisesRegex(ValueError, "invalid_versions"):
            assess_historical_revision(
                versions, decision_at="2026-01-05T12:00:00+00:00")

    def test_empty_list_rejected_with_reason(self):
        result = assess_historical_revision(
            [], decision_at="2026-01-05T12:00:00+00:00")
        self.assertFalse(result["accepted"])
        self.assertIn("no_version_available_asof", result["reasons"])

    def test_tuple_input_remains_supported(self):
        result = assess_historical_revision(
            (ORIGINAL,), decision_at="2026-01-05T12:00:00+00:00")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["revision_id"], "original")

    def test_missing_revision_id_rejected(self):
        missing = {key: value for key, value in ORIGINAL.items() if key != "revision_id"}
        with self.assertRaisesRegex(ValueError, "invalid_revision_id"):
            assess_historical_revision(
                [missing], decision_at="2026-01-05T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
