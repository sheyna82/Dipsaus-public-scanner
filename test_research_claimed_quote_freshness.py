"""Check provider-claimed quote freshness against preserved real market records."""
import json
import tempfile
import unittest
from pathlib import Path
from research_claimed_quote_freshness import audit_preserved_quote_freshness

ROOT=Path(__file__).parent/"research-evidence"
AMD=ROOT/"amd-20261103-source-observation.json"
CSGP=ROOT/"csgp-20261103-source-observation.json"

class ClaimedFreshnessTests(unittest.TestCase):
    def test_real_quotes_are_recent_provider_claims(self):
        report=audit_preserved_quote_freshness([AMD,CSGP])
        self.assertEqual(report["observation_count"],2)
        self.assertEqual([x["symbol"] for x in report["observations"]],["AMD","CSGP"])
        self.assertAlmostEqual(report["observations"][0]["claimed_lag_seconds"],18.430309)
        self.assertAlmostEqual(report["observations"][1]["claimed_lag_seconds"],19.602504)
        self.assertTrue(report["all_within_claimed_lag_threshold"])
        self.assertFalse(report["independent_timestamp_proof"])
        self.assertFalse(report["trade_ready"])

    def test_negative_lag_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"altered.json"
            record=json.loads(CSGP.read_text())
            record["response_finished_utc"]="2026-11-03T20:00:00+00:00"
            p.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,"provider_timestamp_after_capture"):
                audit_preserved_quote_freshness([p])

    def test_tighter_threshold_does_not_imply_verified(self):
        report=audit_preserved_quote_freshness([AMD,CSGP],maximum_claimed_lag_seconds=10)
        self.assertFalse(report["all_within_claimed_lag_threshold"])
        self.assertFalse(report["trade_ready"])

if __name__=="__main__": unittest.main()
