"""Offline AST inventory of legacy EU research calculation entry points.

Audit only: historical call sites are reported, not silently rewritten.
"""
import ast
import json
import pathlib
import subprocess

LEGACY = {
    "research_europe_relative_strength": "compare",
    "research_europe_recovery_confirmation": "evaluate",
}

def inventory(paths):
    hits = []
    for path in sorted(map(pathlib.Path, paths)):
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            raise ValueError("UNPARSABLE_PYTHON_SOURCE:" + str(path)) from exc
        aliases = {}
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    if item.name in LEGACY:
                        aliases[item.asname or item.name] = item.name
            elif isinstance(node, ast.ImportFrom) and node.module in LEGACY:
                for item in node.names:
                    if item.name == LEGACY[node.module]:
                        functions[item.asname or item.name] = node.module
        # Local bindings can shadow module-level legacy imports. Flag this
        # uncertainty rather than treating the name as a proven legacy call.
        for scope in ast.walk(tree):
            if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            parameters = scope.args.posonlyargs + scope.args.args + scope.args.kwonlyargs
            if scope.args.vararg:
                parameters.append(scope.args.vararg)
            if scope.args.kwarg:
                parameters.append(scope.args.kwarg)
            shadowed = {arg.arg for arg in parameters}
            for child in ast.walk(scope):
                if child is scope or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    continue
                if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                    shadowed.add(child.id)
            for name in sorted(shadowed.intersection(set(aliases) | set(functions))):
                hits.append({"path": str(path), "line": scope.lineno,
                             "target": "ambiguous_legacy_scope_shadow:" + name,
                             "kind": "ambiguous_scope"})
        # Track simple function aliases, including chained assignments, without
        # pretending to solve arbitrary Python runtime data flow.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                module = None
                if isinstance(value, ast.Name):
                    module = functions.get(value.id)
                elif (isinstance(value, ast.Attribute) and
                      isinstance(value.value, ast.Name) and value.value.id in aliases):
                    candidate = aliases[value.value.id]
                    if value.attr == LEGACY[candidate]:
                        module = candidate
                if module:
                    for target in targets:
                        if isinstance(target, ast.Name):
                            functions[target.id] = module
        # Rebinding an imported function name to an unrelated value makes
        # AST-wide alias inference ambiguous. Report it rather than claiming
        # the apparent calls are conclusively legacy calls.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name) or target.id not in functions:
                        continue
                    value = node.value
                    source = None
                    if isinstance(value, ast.Name):
                        source = functions.get(value.id)
                    elif (isinstance(value, ast.Attribute) and
                          isinstance(value.value, ast.Name) and value.value.id in aliases):
                        module = aliases[value.value.id]
                        if value.attr == LEGACY[module]:
                            source = module
                    if source != functions[target.id]:
                        hits.append({"path": str(path), "line": node.lineno,
                                     "target": "ambiguous_legacy_alias_rebinding",
                                     "kind": "ambiguous_alias"})
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            dynamic = ((isinstance(node.func, ast.Name) and node.func.id == "__import__") or
                       (isinstance(node.func, ast.Attribute) and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == "importlib" and
                        node.func.attr == "import_module"))
            if dynamic and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value in LEGACY:
                        hits.append({"path": str(path), "line": node.lineno,
                                     "target": arg.value + "." + LEGACY[arg.value],
                                     "kind": "dynamic_import"})
                else:
                    hits.append({"path": str(path), "line": node.lineno,
                                 "target": "unknown_dynamic_import",
                                 "kind": "dynamic_import"})
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
                obj, attribute = node.args[:2]
                if isinstance(obj, ast.Name) and obj.id in aliases:
                    module = aliases[obj.id]
                    if isinstance(attribute, ast.Constant) and attribute.value == LEGACY[module]:
                        hits.append({"path": str(path), "line": node.lineno,
                                     "target": module + "." + LEGACY[module],
                                     "kind": "reflective_access"})
                    elif not isinstance(attribute, ast.Constant):
                        hits.append({"path": str(path), "line": node.lineno,
                                     "target": "unknown_reflective_access",
                                     "kind": "reflective_access"})
            if isinstance(node.func, ast.Name) and node.func.id in ("exec", "eval") and node.args:
                arg = node.args[0]
                if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                    hits.append({"path": str(path), "line": node.lineno,
                                 "target": "unknown_dynamic_code", "kind": "dynamic_code"})
                elif any(module in arg.value for module in LEGACY):
                    hits.append({"path": str(path), "line": node.lineno,
                                 "target": "legacy_dynamic_code", "kind": "dynamic_code"})
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = None
            if isinstance(node.func, ast.Name) and node.func.id in functions:
                target = functions[node.func.id] + "." + LEGACY[functions[node.func.id]]
            elif (isinstance(node.func, ast.Attribute) and
                  isinstance(node.func.value, ast.Name) and
                  node.func.value.id in aliases and
                  node.func.attr == LEGACY[aliases[node.func.value.id]]):
                target = aliases[node.func.value.id] + "." + node.func.attr
            if target:
                hits.append({"path": str(path), "line": node.lineno, "target": target})
    return hits

def tracked_python_files():
    result = subprocess.run(["git", "ls-files", "-z", "--", "*.py"],
                            check=True, capture_output=True)
    return [pathlib.Path(p.decode("utf-8")) for p in result.stdout.split(b"\0") if p]

if __name__ == "__main__":
    print(json.dumps({"schema": "dipsaus_legacy_eu_calls_ast_v1",
                      "audit_only": True, "historical_interfaces_unchanged": True,
                      "call_sites": inventory(tracked_python_files())},
                     indent=2, sort_keys=True))
