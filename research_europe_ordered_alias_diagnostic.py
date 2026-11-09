"""Conservative, offline, order-sensitive diagnostic for top-level legacy aliases.

This is supplemental evidence, not a replacement for the fail-closed gate.
"""
import ast
from research_audit_europe_legacy_calls import LEGACY


def diagnose(source):
    tree = ast.parse(source)
    state = {}
    findings = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for item in stmt.names:
                if item.name in LEGACY:
                    state[item.asname or item.name] = ("module", item.name)
        elif isinstance(stmt, ast.ImportFrom) and stmt.module in LEGACY:
            for item in stmt.names:
                if item.name == LEGACY[stmt.module]:
                    state[item.asname or item.name] = ("function", stmt.module)
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            value = stmt.value
            resolved = None
            if isinstance(value, ast.Name):
                resolved = state.get(value.id)
            elif isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                base = state.get(value.value.id)
                if base and base[0] == "module" and value.attr == LEGACY[base[1]]:
                    resolved = ("function", base[1])
            # Calls inside assignment expressions may execute before binding,
            # but their target is not proven by this supplemental analysis.
            if value is not None:
                for child in ast.walk(value):
                    if isinstance(child, ast.Call):
                        findings.append({"line": child.lineno, "target": None,
                                         "classification": "uncertain_expression_call"})
            for target in targets:
                if isinstance(target, ast.Name):
                    state[target.id] = resolved
        elif isinstance(stmt, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                               ast.With, ast.AsyncWith, ast.Match)):
            # Do not infer which branch ran or how often a loop executed.
            # Invalidate earlier bindings: the compound statement may rebind
            # aliases through nested statements, imports or side effects.
            state.clear()
            findings.append({"line": stmt.lineno, "target": None,
                             "classification": "uncertain_control_flow"})
            # Inventory nested calls without attributing a runtime target.
            # Nested definitions are separate scopes and are not traversed.
            pending = list(ast.iter_child_nodes(stmt))
            while pending:
                child = pending.pop()
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(child, ast.Call):
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_nested_call"})
                pending.extend(ast.iter_child_nodes(child))
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            # The outer call is classified below; its nested arguments and
            # callable expression are inventoried separately as uncertain.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.Call) and child is not stmt.value:
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
            func = stmt.value.func
            resolved = state.get(func.id) if isinstance(func, ast.Name) else None
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                base = state.get(func.value.id)
                if base and base[0] == "module" and func.attr == LEGACY[base[1]]:
                    resolved = ("function", base[1])
            if resolved and resolved[0] == "function":
                findings.append({"line": stmt.lineno,
                                 "target": resolved[1] + "." + LEGACY[resolved[1]],
                                 "classification": "ordered_legacy_call"})
            else:
                findings.append({"line": stmt.lineno, "target": None,
                                 "classification": "not_proven_legacy"})
    return findings
