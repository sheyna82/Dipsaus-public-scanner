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
                # Any import binds its local name, including non-legacy imports.
                # A dotted import without an alias binds its first component.
                bound = item.asname or item.name.split(".")[0]
                state[bound] = (("module", item.name)
                                if item.name in LEGACY else None)
        elif isinstance(stmt, ast.ImportFrom):
            for item in stmt.names:
                if item.name == "*":
                    # Unknown wildcard bindings may shadow any known alias.
                    state.clear()
                    continue
                bound = item.asname or item.name
                state[bound] = (("function", stmt.module)
                                if stmt.module in LEGACY
                                and item.name == LEGACY[stmt.module]
                                else None)
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
                elif isinstance(target, (ast.Tuple, ast.List)):
                    # Unpacking binds each contained name. Without evaluating
                    # the RHS shape, no element retains a proven alias.
                    for child in ast.walk(target):
                        if isinstance(child, ast.Name):
                            state[child.id] = None
            # Assignment RHS may itself bind names through :=. Such bindings
            # can shadow earlier imports, regardless of the outer targets.
            if value is not None:
                for child in ast.walk(value):
                    if isinstance(child, ast.NamedExpr):
                        state[child.target.id] = None
        elif isinstance(stmt, ast.AugAssign):
            # Augmented assignment may mutate or replace an alias. Never
            # retain a previously proven binding after this statement.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.Call):
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
            if isinstance(stmt.target, ast.Name):
                state[stmt.target.id] = None
            else:
                # Attribute/subscript writes can have side effects; avoid
                # preserving unrelated proofs without modeling those effects.
                state.clear()
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
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Defining a function binds its name and shadows any prior import.
            # Even a decorated function cannot retain an earlier alias proof.
            state[stmt.name] = None
            # Decorators, default values and annotations are evaluated at
            # definition time (subject to postponed annotation semantics).
            # Never classify these as deferred body execution.
            definition_expressions = (
                list(stmt.decorator_list)
                + list(stmt.args.defaults)
                + [value for value in stmt.args.kw_defaults if value is not None]
                + [arg.annotation for arg in (
                    stmt.args.posonlyargs + stmt.args.args + stmt.args.kwonlyargs
                    + ([stmt.args.vararg] if stmt.args.vararg else [])
                    + ([stmt.args.kwarg] if stmt.args.kwarg else []))
                   if arg.annotation is not None]
                + ([stmt.returns] if stmt.returns is not None else [])
            )
            for expression in definition_expressions:
                for nested in ast.walk(expression):
                    if isinstance(nested, ast.Call):
                        findings.append({"line": nested.lineno, "target": None,
                                         "classification": "uncertain_definition_time_call"})
            # Return expressions are deferred until invocation; record their
            # syntactic calls without claiming execution or alias identity.
            pending_expressions = list(stmt.body)
            while pending_expressions:
                child = pending_expressions.pop()
                # A nested definition has its own deferred execution context.
                # Do not attribute its returns or conditions to this function.
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(child, (ast.Return, ast.If, ast.While, ast.Assert)):
                    expressions = ([child.value] if isinstance(child, ast.Return)
                                   else [child.test])
                    for expression in expressions:
                        if expression is None:
                            continue
                        for nested in ast.walk(expression):
                            if isinstance(nested, ast.Call):
                                findings.append({"line": nested.lineno, "target": None,
                                                 "classification": "uncertain_deferred_expression_call"})
                pending_expressions.extend(ast.iter_child_nodes(child))
            # Also inspect direct expression statements in the function body;
            # these execute only if the function is invoked.
            pending = list(stmt.body)
            while pending:
                child = pending.pop()
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(child, ast.Expr):
                    for nested in ast.walk(child.value):
                        if isinstance(nested, ast.Call):
                            findings.append({"line": nested.lineno, "target": None,
                                             "classification": "uncertain_deferred_body_call"})
                else:
                    pending.extend(ast.iter_child_nodes(child))
        elif isinstance(stmt, ast.ClassDef):
            # Creating a class binds its name and shadows a previous import.
            # Decorators can also replace the class, so never retain proof.
            state[stmt.name] = None
            # Top-level class decorators, bases and keyword values are also
            # evaluated during class creation, before its body is executed.
            for expression in (list(stmt.decorator_list) + list(stmt.bases)
                               + [kw.value for kw in stmt.keywords]):
                for nested in ast.walk(expression):
                    if isinstance(nested, ast.Call):
                        findings.append({"line": nested.lineno, "target": None,
                                         "classification": "uncertain_class_body_call"})
            # Class body statements execute during class creation, unlike
            # ordinary method bodies. Inspect only direct class-body calls.
            pending_classes = [stmt]
            while pending_classes:
                current_class = pending_classes.pop()
                for member in current_class.body:
                    if isinstance(member, ast.ClassDef):
                        pending_classes.append(member)
                    if isinstance(member, ast.Expr):
                        expressions = [member.value]
                    elif isinstance(member, (ast.Assign, ast.AnnAssign)):
                        expressions = [member.value] if member.value is not None else []
                    elif isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Method body is deferred; decorators and defaults
                        # execute while its enclosing class is created.
                        expressions = (list(member.decorator_list)
                                       + list(member.args.defaults)
                                       + [v for v in member.args.kw_defaults if v is not None])
                    elif isinstance(member, ast.ClassDef):
                        expressions = (list(member.decorator_list) + list(member.bases)
                                       + [kw.value for kw in member.keywords])
                    else:
                        expressions = []
                    for expression in expressions:
                        for nested in ast.walk(expression):
                            if isinstance(nested, ast.Call):
                                findings.append({"line": nested.lineno, "target": None,
                                                 "classification": "uncertain_class_body_call"})
        elif isinstance(stmt, (ast.Assert,)):
            for child in ast.walk(stmt.test):
                if isinstance(child, ast.Call):
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            # A walrus binding in the call expression may shadow a previously
            # proven alias. Do not infer evaluation order or runtime identity.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.NamedExpr):
                    state[child.target.id] = None
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
        elif isinstance(stmt, ast.Expr):
            # Non-call expressions may still bind names via walrus operators,
            # e.g. a conditional expression or an f-string. Invalidate these
            # bindings without attributing the calls inside the expression.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.NamedExpr):
                    state[child.target.id] = None
                if isinstance(child, ast.Call):
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
    return findings
