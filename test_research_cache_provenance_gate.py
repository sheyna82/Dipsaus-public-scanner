"""Offline provenance gate regression tests."""

import unittest

from research_cache_provenance_gate import assess_cached_observation



IDENTITY = {
    "security_id": "synthetic-issuer-1",
    "market": "EU",
    "provider": "test-provider",
    "interval": "1m",
    "adjustment": "raw",
    "dataset_version": "v1",
}


class CacheProvenanceTests(unittest.TestCase):
    def check(self, changes=None, **kwargs):
        cached = {
            **IDENTITY,
            "observed_at": "2026-10-23T09:00:00+00:00",
            **(changes or {}),
        }
        return assess_cached_observation(
            IDENTITY, cached, now="2026-10-23T09:01:00+00:00",
            max_age_seconds=120, **kwargs,
        )

    def test_fresh_matching_identity(self):
        result = self.check()
        self.assertTrue(result["accepted"])
        self.assertFalse(result["provider_authenticity_verified"])

    def test_provider_mismatch(self):
        self.assertIn("identity_mismatch_provider", self.check({"provider": "other"})["reasons"])

    def test_stale_observation(self):
        self.assertIn("stale_observation", self.check({"observed_at": "2026-10-23T08:00:00+00:00"})["reasons"])

    def test_future_observation(self):
        self.assertIn("future_observation", self.check({"observed_at": "2026-10-23T09:02:00+00:00"})["reasons"])

    def test_missing_timestamp(self):
        self.assertIn("invalid_observation_time", self.check({"observed_at": None})["reasons"])


if __name__ == "__main__":
    unittest.main()
