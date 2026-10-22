import unittest
from dipsaus_offline_event_batch import evaluate_event_batch


def row(symbol="META", event_id="q3", phase="POST_EVENT", confirmed=False,
        risk=False, **extras):
    value = {"symbol": symbol, "event_id": event_id, "event_phase": phase,
             "quote_fresh": True, "event_verified": True,
             "trend_confirmed": confirmed, "downside_warning": risk}
    value.update(extras)
    return value


def prior(symbol="META", event_id="q3"):
    return {symbol + ":" + event_id: {
        "status": "RESEARCH_ONLY", "symbol": symbol, "event_id": event_id,
        "classification": "WAIT_CONFIRMATION"}}


class EventBatchTests(unittest.TestCase):
    def test_duplicate_event_yields_one_review(self):
        result = evaluate_event_batch([row(confirmed=True, category="research"),
                                       row(confirmed=True, category="company")], prior())
        self.assertEqual(len(result["review_candidates"]), 1)
        self.assertEqual(result["events_considered"], 1)

    def test_risk_wins_duplicate(self):
        result = evaluate_event_batch([row(confirmed=True), row(risk=True)], prior())
        self.assertEqual(result["review_candidates"][0]["classification"], "RISK_ELEVATED")

    def test_no_baseline_no_alert(self):
        result = evaluate_event_batch([row(confirmed=True)])
        self.assertEqual(result["review_candidates"], [])

    def test_stale_is_blocked(self):
        result = evaluate_event_batch([row(quote_fresh=False)], prior())
        self.assertEqual(len(result["blocked"]), 1)
        self.assertEqual(result["review_candidates"], [])

    def test_conflicting_phase_blocks(self):
        result = evaluate_event_batch([row(confirmed=True),
                                       row(phase="PRE_EVENT")], prior())
        self.assertEqual(result["review_candidates"], [])
        self.assertEqual(result["blocked"][0]["reason"], "conflicting_event_phase")


if __name__ == "__main__":
    unittest.main()
