"""Offline tests for the isolated Spoor 2 ntfy classification policy."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "research" / "spoor2_notification_policy_20261111.py"
spec = importlib.util.spec_from_file_location("spoor2_ntfy", path)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class NotificationPolicyTests(unittest.TestCase):
    def qualified(self):
        data = {k: True for k in policy.TRADE_EVIDENCE}
        data.update(phase="BREAKOUT-HOLD-RETEST", trade_ready=True,
                    rr_verified=True, net_profit_verified=True,
                    rr=2.1, net_profit_eur=160)
        return data

    def test_phase_is_research_only(self):
        for phase in policy.RESEARCH_PHASES:
            self.assertEqual(policy.classify_notification({"phase": phase})["channel"],
                             "RESEARCH")

    def test_complete_independent_evidence_is_review_only(self):
        result = policy.classify_notification(self.qualified())
        self.assertEqual(result["channel"], "TRADE_QUALIFIED_REVIEW")
        self.assertFalse(result["order_placement_enabled"])

    def test_every_missing_gate_blocks(self):
        for field in (*policy.TRADE_EVIDENCE, "trade_ready", "rr_verified",
                      "net_profit_verified"):
            data = self.qualified()
            del data[field]
            self.assertEqual(policy.classify_notification(data)["channel"],
                             "RESEARCH", field)

    def test_below_thresholds_block(self):
        for key, value in (("rr", 1.99), ("net_profit_eur", 149.99),
                           ("rr", float("nan")), ("rr", True)):
            data = self.qualified()
            data[key] = value
            self.assertEqual(policy.classify_notification(data)["channel"], "RESEARCH")

    def test_titles_distinguish_channels(self):
        research = policy.classify_notification({"phase": "BREAKOUT-SEEN"})
        self.assertIn("GEEN KOOP", policy.notification_subject("BTE", research))
        qualified = policy.classify_notification(self.qualified())
        self.assertIn("GECONTROLEERDE INSTAPCHECK",
                      policy.notification_subject("BTE", qualified))

    def test_offline_topics_are_logically_separate(self):
        research=policy.offline_notification_route(
            policy.classify_notification({"phase":"BREAKOUT-SEEN"}))
        review=policy.offline_notification_route(
            policy.classify_notification(self.qualified()))
        self.assertEqual(research["route"],"RESEARCH_ONLY")
        self.assertEqual(review["route"],"INDEPENDENT_REVIEW_ONLY")
        self.assertNotEqual(research["route"],review["route"])
        for result in (research,review):
            self.assertFalse(result["send_enabled"])
            self.assertFalse(result["topic_configured"])
            self.assertFalse(result["order_placement_enabled"])

    def test_untrusted_classifications_cannot_route(self):
        for item in (None,{},{"channel":"RESEARCH","qualified":True},
                     {"channel":"TRADE_QUALIFIED_REVIEW","qualified":True},
                     {"channel":"TRADE_QUALIFIED_REVIEW",
                      "qualified":True,"order_placement_enabled":True}):
            with self.subTest(item=item):
                r=policy.offline_notification_route(item)
                self.assertEqual(r["route"],"NONE")
                self.assertFalse(r["send_enabled"])

    def test_unknown_input_is_not_sent(self):
        self.assertEqual(policy.classify_notification({})["channel"], "NONE")
        self.assertEqual(policy.classify_notification(None)["channel"], "NONE")


if __name__ == "__main__":
    unittest.main()
