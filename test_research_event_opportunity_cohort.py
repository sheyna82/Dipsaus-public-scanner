"""Regression checks for fixed, non-trading event opportunity cohort."""
import unittest
from research_event_opportunity_cohort import build_event_study


class EventCohortTests(unittest.TestCase):
    def test_six_notifications_and_no_trading(self):
        result = build_event_study()
        self.assertEqual(
            {x["symbol"] for x in result["records"]},
            {"TSLA", "META", "COHU", "AMZN", "PLTR", "AMD"})
        self.assertFalse(result["live_notifications_enabled"])
        self.assertFalse(result["automatic_orders"])
        self.assertTrue(all(not x["trade_ready"] and
                            not x["prediction_issued"] and
                            not x["outcomes_measured"]
                            for x in result["records"]))

    def test_retroactive_events_are_not_forward_predictions(self):
        result = build_event_study()
        phase = {x["symbol"]: x["event_phase"] for x in result["records"]}
        self.assertEqual(phase["TSLA"], "RETROSPECTIVE")
        self.assertEqual(phase["META"], "RETROSPECTIVE")
        self.assertEqual(phase["AMD"], "PROSPECTIVE")
        self.assertEqual(phase["COHU"], "PROSPECTIVE")

    def test_missing_inputs_remain_missing(self):
        record = build_event_study(evidence_by_symbol={
            "AMD": {"fresh_quote": 100}
        })["records"][-1]
        self.assertNotIn("fresh_quote", record["missing_evidence"])
        self.assertIn("quote_timestamp_utc", record["missing_evidence"])
        self.assertFalse(record["pre_event_snapshot_verified"])
        self.assertFalse(record["exchange_calendar_verified"])

    def test_invalid_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, "event_evidence_must_be_mapping"):
            build_event_study(evidence_by_symbol={"AMD": [1, 2]})


if __name__ == "__main__":
    unittest.main()
