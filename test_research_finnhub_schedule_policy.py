"""Offline scheduling safety tests: no network, secrets, or actions."""
import unittest
from datetime import datetime, timedelta, timezone
from research_finnhub_schedule_policy import evaluate_schedule, safe_default

NOW = datetime(2026, 11, 3, 20, 0, tzinfo=timezone.utc)


class SchedulePolicyTests(unittest.TestCase):
    def check(self, **changes):
        args = dict(symbol="AMD", now=NOW, prior_utc=[], daily_count=0, enabled=True)
        args.update(changes)
        return evaluate_schedule(**args)

    def test_default_disabled(self):
        self.assertEqual(safe_default()["reason"], "not_approved_for_automation")

    def test_explicitly_disabled(self):
        self.assertFalse(self.check(enabled=False)["eligible"])

    def test_supported_symbol_with_explicit_enablement(self):
        self.assertEqual(self.check(), {"eligible": True, "reason": "offline_policy_only"})

    def test_reject_unknown_symbol(self):
        self.assertFalse(self.check(symbol="INVALID")["eligible"])

    def test_reject_non_utc_time(self):
        self.assertEqual(self.check(now=NOW.replace(tzinfo=None))["reason"], "utc_required")

    def test_reject_daily_limit(self):
        self.assertEqual(self.check(daily_count=4)["reason"], "daily_capacity_unavailable")

    def test_reject_invalid_count(self):
        self.assertFalse(self.check(daily_count=True)["eligible"])

    def test_reject_duplicate_within_interval(self):
        self.assertEqual(self.check(prior_utc=[NOW - timedelta(minutes=10)])["reason"], "duplicate_or_too_soon")

    def test_accept_interval_boundary(self):
        self.assertTrue(self.check(prior_utc=[NOW - timedelta(minutes=30)])["eligible"])

    def test_reject_future_observation(self):
        self.assertEqual(self.check(prior_utc=[NOW + timedelta(seconds=1)])["reason"], "future_observation")

    def test_reject_invalid_history(self):
        self.assertFalse(self.check(prior_utc=[NOW.replace(tzinfo=None)])["eligible"])


if __name__ == "__main__":
    unittest.main()
