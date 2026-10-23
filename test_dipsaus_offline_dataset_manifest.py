import unittest
from datetime import datetime, timezone, timedelta
from dipsaus_offline_dataset_manifest import validate_dataset_manifest


def manifest():
    return {"provider": "example-data", "source_url": "https://example.org/data",
            "license_name": "example-license", "license_url": "https://example.org/license",
            "retrieved_at": "2026-10-20T12:00:00+00:00",
            "price_adjustment": "split_adjusted", "timezone": "America/New_York",
            "survivorship_policy": "includes_delisted",
            "corporate_actions_policy": "adjusted_with_event_history",
            "point_in_time_policy": "verified_release_timestamps",
            "universe_definition": "documented_asof_universe"}


class ManifestTests(unittest.TestCase):
    def test_complete_manifest_not_independently_verified(self):
        result = validate_dataset_manifest(manifest())
        self.assertTrue(result["accepted"])
        self.assertFalse(result["source_verified"])
        self.assertFalse(result["trade_ready"])

    def test_missing_license_rejected(self):
        x = manifest()
        del x["license_url"]
        self.assertFalse(validate_dataset_manifest(x)["accepted"])

    def test_survivorship_and_point_in_time_gates(self):
        x = manifest()
        x["survivorship_policy"] = "survivors_only"
        x["point_in_time_policy"] = "unknown"
        r = validate_dataset_manifest(x)
        self.assertIn("survivorship_bias_unaddressed", r["errors"])
        self.assertIn("point_in_time_unverified", r["errors"])

    def test_bad_url_and_future_timestamp(self):
        x = manifest()
        x["source_url"] = "http://example.org"
        x["retrieved_at"] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        r = validate_dataset_manifest(x)
        self.assertIn("invalid_source_url", r["errors"])
        self.assertIn("future_retrieval_timestamp", r["errors"])


if __name__ == "__main__":
    unittest.main()
