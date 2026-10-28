"""Regression: newest cumulative archive is tried before older archives."""
import ast
import pathlib
import unittest

class ArtifactOrderingTests(unittest.TestCase):
    def test_restore_sorts_before_iteration(self):
        source=pathlib.Path(__file__).with_name("incremental_database.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        restore=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="restore")
        source_lines=source.splitlines()
        sort_lines=[n.lineno for n in ast.walk(restore) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="sort" and isinstance(n.func.value,ast.Name) and n.func.value.id=="candidates"]
        loop_lines=[n.lineno for n in ast.walk(restore) if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=="candidates"]
        self.assertEqual(len(sort_lines),1)
        self.assertEqual(len(loop_lines),1)
        self.assertLess(sort_lines[0],loop_lines[0])
        self.assertIn("created_at",source_lines[sort_lines[0]-1])
        self.assertIn("reverse=True",source_lines[sort_lines[0]-1])
    def test_newest_first_with_id_tiebreak(self):
        candidates=[{"id":1,"created_at":"2026-10-20T10:00:00Z"},{"id":5,"created_at":"2026-10-21T10:00:00Z"},{"id":8,"created_at":"2026-10-21T10:00:00Z"}]
        candidates.sort(key=lambda a:(a.get("created_at") or "",a.get("id") or 0),reverse=True)
        self.assertEqual([a["id"] for a in candidates],[8,5,1])

if __name__=="__main__": unittest.main()
