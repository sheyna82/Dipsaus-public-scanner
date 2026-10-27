"""Breadth audit regression tests; no synthetic performance claims."""
import unittest
from research_swing_breadth_audit import audit_research_breadth

def example(symbol="ABC", event_id="1", **extra):
    row = dict(symbol=symbol, market="US", sector="technology", cap_bucket="mid",
               regime="bear", event_kind="earnings_release", event_id=event_id,
               available_at_utc="2020-03-01T20:00:00+00:00",
               source_url="https://example.org/issuer", delisted_included=False)
    row.update(extra)
    return row

class BreadthAuditTests(unittest.TestCase):
    def test_empty_dataset_does_not_claim_coverage(self):
        result = audit_research_breadth([])
        self.assertEqual(result["complete_rows"], 0)
        self.assertEqual(result["coverage"]["market"], {})
    def test_cross_market_coverage(self):
        result = audit_research_breadth([
            example(), example("XYZ", "2", market="FR", sector="energy",
                               delisted_included=True)])
        self.assertEqual(result["coverage"]["market"], {"US": 1, "FR": 1})
        self.assertEqual(result["delisted_included_count"], 1)
    def test_missing_dimensions_reported(self):
        row = example()
        row.pop("sector")
        result = audit_research_breadth([row])
        self.assertEqual(result["complete_rows"], 0)
        self.assertEqual(result["missing_field_counts"]["sector"], 1)
    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_event_identity"):
            audit_research_breadth([example(), example()])
    def test_bad_row_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_row"):
            audit_research_breadth([None])

if __name__ == "__main__":
    unittest.main()
