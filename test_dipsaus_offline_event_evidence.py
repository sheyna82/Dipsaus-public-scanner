import unittest
from dipsaus_offline_event_evidence import build_event_observation
from dipsaus_offline_event_watch import classify_event_observation


def event(**kw):
    v = {"symbol": "tsla", "event_id": "2026-q3",
         "event_phase": "POST_EVENT", "event_verified": True}
    v.update(kw)
    return v


def quote(**kw):
    v = {"quote_fresh": True, "trend_confirmed": False,
         "downside_warning": False}
    v.update(kw)
    return v


class EventEvidenceTests(unittest.TestCase):
    def test_valid_evidence_can_be_classified(self):
        row = build_event_observation(event(), quote())
        self.assertEqual(row["symbol"], "TSLA")
        self.assertEqual(classify_event_observation(row)["classification"],
                         "WAIT_CONFIRMATION")

    def test_missing_confirmation_blocks(self):
        v = quote()
        del v["trend_confirmed"]
        self.assertEqual(build_event_observation(event(), v)["status"], "DATA_BLOCKED")

    def test_stale_quote_blocks(self):
        self.assertEqual(build_event_observation(event(), quote(quote_fresh=False))["status"],
                         "DATA_BLOCKED")

    def test_unverified_event_blocks(self):
        self.assertEqual(build_event_observation(event(event_verified=False), quote())["status"],
                         "DATA_BLOCKED")

    def test_unknown_phase_blocks(self):
        self.assertEqual(build_event_observation(event(event_phase="UNKNOWN"), quote())["status"],
                         "DATA_BLOCKED")

    def test_non_boolean_confirmation_blocks(self):
        self.assertEqual(build_event_observation(event(), quote(trend_confirmed="yes"))["status"],
                         "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
