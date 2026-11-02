"""Synthetic shadow integration: no runner import, network, secrets or orders."""
import ast
from datetime import datetime, timezone
from pathlib import Path
import unittest

from event_quote_gap_summary import summarize_event_quote_gaps


class SyntheticPrivateShadowTests(unittest.TestCase):
    def test_runner_calls_aggregate_before_research_and_never_prints_it(self):
        source = Path("safe_runner.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Subscript)
                               and isinstance(t.value, ast.Name) and t.value.id == "state"
                               and isinstance(t.slice, ast.Constant)
                               and t.slice.value == "latest_event_quote_gap_research"
                               for t in node.targets)]
        self.assertEqual(len(assignments), 2)
        successful = [a for a in assignments if isinstance(a.value, ast.Call)]
        self.assertEqual(len(successful), 1)
        node = successful[0]
        self.assertIsInstance(node.value, ast.Call)
        self.assertEqual(node.value.func.id, "summarize_event_quote_gaps")
        self.assertEqual(len(node.value.args), 2)
        self.assertEqual(len(node.value.keywords), 1)
        self.assertEqual(node.value.keywords[0].arg, "expected_currency")
        self.assertIsInstance(node.value.keywords[0].value, ast.Constant)
        self.assertIsNone(node.value.keywords[0].value.value)
        self.assertNotIn("latest_event_quote_gap_research", source[source.index("# Public logs expose only aggregate"):])

    def test_synthetic_private_state_mixed_currency_no_trade_side_effect(self):
        now = datetime(2026, 11, 2, 15, tzinfo=timezone.utc)
        common = {"provider_quote": 100, "provider_quote_utc": "2026-11-02T14:59:00+00:00",
                  "provider_freshness_pass": True, "provider_source": "synthetic",
                  "market_session_verified": True, "provider_delayed": False}
        rows = [dict(common, symbol="SYN.US", provider_symbol="SYN.US", provider_currency="USD"),
                dict(common, symbol="SYN.EU", provider_symbol="SYN.EU", provider_currency="EUR"),
                {"symbol": "SYN.MISSING"}]
        private_state = {"latest_watch_reports": {"entries": {"rows": rows}}}
        private_state["latest_event_quote_gap_research"] = summarize_event_quote_gaps(
            private_state["latest_watch_reports"]["entries"]["rows"], now, expected_currency=None)
        report = private_state["latest_event_quote_gap_research"]
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["validated_research_only"], 2)
        self.assertEqual(report["blocked"], 1)
        self.assertIs(report["execution_ready"], False)
        self.assertNotIn("SYN.", str(report))
        self.assertIn("provider_quote", report["missing_counts"])
        self.assertNotIn("100", str(report))


if __name__ == "__main__":
    unittest.main()
