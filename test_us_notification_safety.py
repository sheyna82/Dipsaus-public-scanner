"""Regression checks for automatic US discovery notification safety.

These tests use a fake sender/store and never contact ntfy or brokers.
"""
import unittest
from private_notifications import notify


class FakeStore:
    def require_exclusive_sender(self):
        pass
    def save(self, state):
        pass


def us_row(**overrides):
    row = dict(symbol="TEST", market="US", watch_type="AUTO-US-DISCOVERY",
               status="DEGIRO-VERIFY-NOW", phone_notification_eligible=True,
               provider_freshness_pass=True, structure_available=True,
               intraday_hold_confirmed=True, early_turn_observed=True,
               prealert_trigger_observed=True, breakout_observed=True,
               hold_observed=True, provider_quote=100, day_low=98,
               rebound_from_day_low_pct=2)
    row.update(overrides)
    return row


class USNotificationSafetyTest(unittest.TestCase):
    def sends(self, row):
        sent = []
        notify(FakeStore(), {"signals": {}}, [row], [],
               sender=lambda symbol, body: sent.append((symbol, body)))
        return sent

    def test_confirmed_fresh_eligible_trigger_can_notify(self):
        self.assertTrue(self.sends(us_row()))

    def test_silent_follow_never_notifies(self):
        self.assertFalse(self.sends(us_row(phone_notification_eligible=False)))

    def test_stale_provider_never_notifies(self):
        self.assertFalse(self.sends(us_row(provider_freshness_pass=False)))

    def test_missing_structure_never_notifies(self):
        self.assertFalse(self.sends(us_row(structure_available=False)))

    def test_unconfirmed_intraday_hold_never_notifies(self):
        self.assertFalse(self.sends(us_row(intraday_hold_confirmed=False)))

    def test_early_research_requires_freshness(self):
        self.assertFalse(self.sends(us_row(status="EARLY-RECOVERY-WATCH",
                                           prealert_trigger_observed=False,
                                           provider_freshness_pass=False)))


if __name__ == "__main__":
    unittest.main()
