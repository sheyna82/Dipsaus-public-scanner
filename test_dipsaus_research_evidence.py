"""Shadow research adapter: no false clearance from stale or absent data."""
import unittest
from datetime import datetime, timezone, timedelta
from dipsaus_research_evidence import evidence_from_prealert
from dipsaus_unified_research import evaluate


class EvidenceBridgeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 19, 30, tzinfo=timezone.utc)
        self.stamp = self.now.isoformat()
        self.row = dict(symbol="EXE", provider_quote_utc=self.stamp,
                        provider_freshness_pass=True,
                        prealert_trigger_observed=True, recent_volume_ratio=1.8)

    def test_fresh_explicit_trigger_is_caution_not_trade_clearance(self):
        ev = evidence_from_prealert(self.row, self.stamp, self.now)
        self.assertEqual(ev["early_recovery"]["status"], "CAUTION")
        self.assertEqual(ev["volume_confirmation"]["status"], "CAUTION")
        result = evaluate(self.row, ev, now=self.now)
        self.assertEqual(result["research_status"], "INCOMPLETE_RESEARCH")
        self.assertFalse(result["notify"])
        self.assertFalse(result["trade_ready"])

    def test_stale_quote_never_passes(self):
        self.row["provider_quote_utc"] = (self.now-timedelta(minutes=20)).isoformat()
        self.assertEqual(evidence_from_prealert(self.row, self.stamp, self.now), {})

    def test_stale_report_never_passes(self):
        old = (self.now-timedelta(minutes=20)).isoformat()
        self.assertEqual(evidence_from_prealert(self.row, old, self.now), {})

    def test_no_trigger_or_no_volume_is_unknown(self):
        self.row["prealert_trigger_observed"] = False
        self.assertEqual(evidence_from_prealert(self.row, self.stamp, self.now), {})
        self.row["prealert_trigger_observed"] = True
        self.row.pop("recent_volume_ratio")
        self.assertEqual(set(evidence_from_prealert(self.row, self.stamp, self.now)),
                         {"early_recovery"})

    def test_unverified_provider_never_passes(self):
        self.row["provider_freshness_pass"] = False
        self.assertEqual(evidence_from_prealert(self.row, self.stamp, self.now), {})

    def test_missing_timezone_and_future_quote_never_pass(self):
        self.row["provider_quote_utc"] = "2026-10-19T19:30:00"
        self.assertEqual(evidence_from_prealert(self.row, self.stamp, self.now), {})
        self.row["provider_quote_utc"] = (self.now+timedelta(minutes=3)).isoformat()
        self.assertEqual(evidence_from_prealert(self.row, self.stamp, self.now), {})


if __name__ == "__main__":
    unittest.main()
