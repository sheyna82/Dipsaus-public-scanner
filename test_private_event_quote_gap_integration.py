"""Guard private runner event quote gap integration against accidental disclosure."""
import ast
from pathlib import Path
import unittest

class PrivateGapIntegrationTests(unittest.TestCase):
    def test_runner_writes_only_private_research_state(self):
        source = Path("safe_runner.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = [node for node in ast.walk(tree)
                       if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Subscript)
                               and isinstance(t.value, ast.Name)
                               and t.value.id == "state"
                               and isinstance(t.slice, ast.Constant)
                               and t.slice.value == "latest_event_quote_gap_research"
                               for t in node.targets)]
        self.assertEqual(len(assignments), 2)
        calls = [a.value for a in assignments if isinstance(a.value, ast.Call)]
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertIsInstance(call, ast.Call)
        self.assertIsInstance(call.func, ast.Name)
        self.assertEqual(call.func.id, "summarize_event_quote_gaps")
        fallbacks = [a.value for a in assignments if isinstance(a.value, ast.Dict)]
        self.assertEqual(len(fallbacks), 1)
        fallback = ast.literal_eval(fallbacks[0])
        self.assertEqual(fallback["status"], "RESEARCH_ERROR")
        self.assertIs(fallback["execution_ready"], False)
        self.assertIs(fallback["broker_quote_verified"], False)
        self.assertIs(fallback["identity_independently_verified"], False)

if __name__ == "__main__":
    unittest.main()
