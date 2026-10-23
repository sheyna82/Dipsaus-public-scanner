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


    def test_each_identity_dimension_rejected(self):
        for field in IDENTITY:
            with self.subTest(field=field):
                result = self.check({field: "different-value"})
                self.assertFalse(result["accepted"])
                self.assertIn("identity_mismatch_" + field, result["reasons"])

    def test_timezone_offset_equivalence(self):
        result = self.check({"observed_at": "2026-10-23T11:00:00+02:00"})
        self.assertTrue(result["accepted"])
        self.assertEqual(result["age_seconds"], 60)

    def test_naive_timestamp_rejected(self):
        result = self.check({"observed_at": "2026-10-23T09:00:00"})
        self.assertIn("invalid_observation_time", result["reasons"])

    def test_exact_ttl_boundary_accepted(self):
        result = self.check({"observed_at": "2026-10-23T08:59:00+00:00"})
        self.assertTrue(result["accepted"])
        self.assertEqual(result["age_seconds"], 120)

    def test_older_than_ttl_rejected(self):
        result = self.check({"observed_at": "2026-10-23T08:58:59+00:00"})
        self.assertIn("stale_observation", result["reasons"])

    def test_missing_request_identity_rejected(self):
        for field in IDENTITY:
            with self.subTest(field=field):
                request = {k: v for k, v in IDENTITY.items() if k != field}
                with self.assertRaisesRegex(ValueError, "invalid_request_identity"):
                    assess_cached_observation(
                        request, {**IDENTITY, "observed_at": "2026-10-23T09:00:00+00:00"},
                        now="2026-10-23T09:01:00+00:00", max_age_seconds=120,
                    )

    def test_invalid_ttl_rejected(self):
        for ttl in (-1, 86401, True, float("nan")):
            with self.subTest(ttl=ttl):
                with self.assertRaisesRegex(ValueError, "invalid_max_age"):
                    assess_cached_observation(
                        IDENTITY, {**IDENTITY, "observed_at": "2026-10-23T09:00:00+00:00"},
                        now="2026-10-23T09:01:00+00:00", max_age_seconds=ttl,
                    )


if __name__ == "__main__":
    unittest.main()
