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
        self.assertEqual(len(assignments), 1)
        call = assignments[0].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsInstance(call.func, ast.Name)
        self.assertEqual(call.func.id, "safe_quote_gap_research")

if __name__ == "__main__":
    unittest.main()
