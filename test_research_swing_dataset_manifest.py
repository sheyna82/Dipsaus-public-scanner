import unittest
from research_swing_dataset_manifest import validate_research_dataset_manifest

def manifest(**changes):
    m = dict(dataset_id="sample", market="US",
             source_url="https://example.org/data", retrieved_at="2026-10-26T12:00:00Z",
             as_of_at="2026-10-25T12:00:00Z", price_adjustment="split_adjusted",
             currency="USD", includes_delisted=True, license_reviewed=True,
             event_timestamp_policy="independently_verified")
    m.update(changes)
    return m

class DatasetManifestTests(unittest.TestCase):
    def test_eligible_manifest(self):
        self.assertTrue(validate_research_dataset_manifest(manifest())["research_comparison_eligible"])
    def test_survivorship_warning(self):
        result = validate_research_dataset_manifest(manifest(includes_delisted=False))
        self.assertFalse(result["research_comparison_eligible"])
    def test_unreviewed_license(self):
        result = validate_research_dataset_manifest(manifest(license_reviewed=False))
        self.assertFalse(result["research_comparison_eligible"])
    def test_timestamp_policy(self):
        with self.assertRaisesRegex(ValueError, "unverified_event_timestamp_policy"):
            validate_research_dataset_manifest(manifest(event_timestamp_policy="assumed"))
    def test_future_asof(self):
        with self.assertRaisesRegex(ValueError, "future_dataset_asof"):
            validate_research_dataset_manifest(manifest(as_of_at="2026-10-27T12:00:00Z"))
    def test_adjustment_unknown(self):
        with self.assertRaisesRegex(ValueError, "unknown_adjustment"):
            validate_research_dataset_manifest(manifest(price_adjustment="mystery"))

if __name__ == "__main__":
    unittest.main()
