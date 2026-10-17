"""No-network EU research freshness regression tests."""
import unittest
from datetime import datetime, timedelta, timezone
from private_notifications import notify_eu_research


class Store:
    def require_exclusive_sender(self):
        pass
    def save(self, state):
        pass


def report(age_minutes):
    return {
        "generated_utc": (datetime.now(timezone.utc) - timedelta(minutes=age_minutes)).isoformat(),
        "candidates": [{
            "symbol": "TEST.PA", "broker_verify_now": True,
            "broker_check_candidate": True, "trade_ready": False,
            "provider_freshness_pass": True, "early_recovery_score": 4,
            "historical_flags": [],
            "historical_3500_eur_scenarios": {
                "rr_to_meaningful": 2.5,
                "meaningful_resistance_gross_eur": 180,
            },
        }],
    }


class EUFreshnessSafetyTest(unittest.TestCase):
    def count(self, data):
        sent = []
        notify_eu_research(Store(), {"signals": {}}, data, set(),
                           sender=lambda symbol, body: sent.append((symbol, body)))
        return len(sent)

    def test_fresh_research_can_reach_mock_sender(self):
        self.assertEqual(self.count(report(1)), 1)

    def test_expired_research_cannot_notify(self):
        self.assertEqual(self.count(report(26)), 0)

    def test_future_dated_research_cannot_notify(self):
        self.assertEqual(self.count(report(-2)), 0)

    def test_missing_timestamp_cannot_notify(self):
        data = report(1)
        del data["generated_utc"]
        self.assertEqual(self.count(data), 0)

    def test_stale_quote_cannot_notify_even_with_fresh_report(self):
        data = report(1)
        data["candidates"][0]["provider_freshness_pass"] = False
        self.assertEqual(self.count(data), 0)


if __name__ == "__main__":
    unittest.main()
