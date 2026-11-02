"""Fault injection into the isolated research boundary, no scanner startup."""
import unittest
from datetime import datetime, timezone
from event_quote_gap_boundary import safe_quote_gap_research


class QuoteGapBoundaryFaultTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 15, tzinfo=timezone.utc)
        self.rows = [{"symbol": "PRIVATE-SYNTH", "provider_quote": 123.45}]

    def test_injected_exception_is_redacted_and_nonfatal(self):
        def broken(*args, **kwargs):
            raise RuntimeError("PRIVATE-SYNTH 123.45 sensitive detail")
        result = safe_quote_gap_research(self.rows, self.now, summarize=broken)
        self.assertEqual(result["status"], "RESEARCH_ERROR")
        self.assertIs(result["execution_ready"], False)
        self.assertIs(result["broker_quote_verified"], False)
        self.assertNotIn("PRIVATE-SYNTH", str(result))
        self.assertNotIn("123.45", str(result))

    def test_untrusted_execution_ready_result_fails_closed(self):
        result = safe_quote_gap_research(self.rows, self.now,
                    summarize=lambda *a, **k: {"execution_ready": True})
        self.assertEqual(result["status"], "RESEARCH_ERROR")
        self.assertIs(result["execution_ready"], False)

    def test_real_summary_remains_research_only(self):
        result = safe_quote_gap_research(self.rows, self.now)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertEqual(result["blocked"], 1)
        self.assertIs(result["execution_ready"], False)


if __name__ == "__main__":
    unittest.main()
