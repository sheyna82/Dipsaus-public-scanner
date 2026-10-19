import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from silent_macro_context import classify, update_silent_context

class SilentMacroTests(unittest.TestCase):
    def test_categorization_and_no_alert(self):
        state = {}
        now = datetime(2026, 10, 19, tzinfo=timezone.utc)
        with patch.dict("os.environ", {"FINNHUB_API_KEY": "dummy"}):
            result = update_silent_context(state, now=now,
                fetch=lambda: [{"headline": "White House announces tariff pause", "source": "example", "datetime": 1}])
        self.assertEqual(result["status"], "HEADLINE_REVIEW_ONLY")
        self.assertEqual(result["headlines"][0]["categories"], ["trade_policy", "fiscal_policy"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["notify"])
        self.assertEqual(state["silent_macro_context"], result)

    def test_hourly_cache(self):
        state = {}
        now = datetime(2026, 10, 19, tzinfo=timezone.utc)
        update_silent_context(state, now=now, fetch=lambda: [])
        def fail():
            raise AssertionError("must not refetch")
        update_silent_context(state, now=now + timedelta(minutes=30), fetch=fail)

    def test_unavailable_fails_closed(self):
        result = update_silent_context({}, fetch=lambda: (_ for _ in ()).throw(OSError()))
        self.assertEqual(result["status"], "PROVIDER_UNAVAILABLE")
        self.assertFalse(result["notify"])
