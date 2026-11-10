"""Conservative, offline, order-sensitive diagnostic for top-level legacy aliases.

This is supplemental evidence, not a replacement for the fail-closed gate.
"""
import ast
from research_audit_europe_legacy_calls import LEGACY


def _scan_class_creation_expressions(expressions, state, findings, module_scope=False,
                                     local_lambdas=None):
    """Conservatively scan expressions evaluated while a class is created.

    Deferred function and lambda bodies are not class-creation effects.
    """
    for expression in expressions:
        if expression is None:
            continue
        pending = [expression]
        while pending:
            node = pending.pop()
            if isinstance(node, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "exec":
                    state.clear()
                # An immediately invoked lambda executes its body during
                # class creation. Merely constructing a lambda does not.
                if isinstance(node.func, ast.Lambda):
                    pending.append(node.func.body)
                elif (isinstance(node.func, ast.Name) and local_lambdas is not None
                      and node.func.id in local_lambdas):
                    pending.append(local_lambdas[node.func.id].body)
                findings.append({"line": node.lineno, "target": None,
                                 "classification": "uncertain_class_body_call"})
            # Class headers at module scope bind in the module; expressions
            # evaluated inside a class body bind in that class namespace.
            if isinstance(node, ast.NamedExpr) and module_scope:
                state[node.target.id] = None
            pending.extend(ast.iter_child_nodes(node))


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
                                if stmt.level == 0 and stmt.module in LEGACY
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
                    # A bare annotation (name: Type) does not assign a value
                    # or replace a previously imported runtime binding.
                    if not (isinstance(stmt, ast.AnnAssign) and value is None):
                        state[target.id] = resolved
                elif isinstance(target, (ast.Tuple, ast.List)):
                    # Unpacking binds each contained name. Without evaluating
                    # the RHS shape, no element retains a proven alias.
                    for child in ast.walk(target):
                        if isinstance(child, ast.Name):
                            state[child.id] = None
                    if any(isinstance(child, (ast.Attribute, ast.Subscript))
                           for child in ast.walk(target)):
                        # Assignment through a property or __setitem__ may
                        # execute arbitrary code that changes other aliases.
                        state.clear()
                else:
                    # Attribute/subscript assignment can execute user code.
                    # Never preserve unrelated alias proofs across it.
                    state.clear()
            if isinstance(stmt, ast.AnnAssign):
                # Annotation expressions may be evaluated at module scope.
                # Even without a value, a walrus may shadow a prior alias.
                # Postponed annotations make execution uncertain, not proven.
                for child in ast.walk(stmt.annotation):
                    if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                            and child.func.id == "exec"):
                        # Runtime annotation evaluation may execute code that
                        # rebinds module aliases; postponed evaluation is
                        # uncertain, so never retain an unqualified proof.
                        state.clear()
                    if isinstance(child, ast.NamedExpr):
                        state[child.target.id] = None
                    if isinstance(child, ast.Call):
                        findings.append({"line": child.lineno, "target": None,
                                         "classification": "uncertain_expression_call"})
            # Assignment RHS may itself bind names through :=. Such bindings
            # can shadow earlier imports, regardless of the outer targets.
            if value is not None:
                for child in ast.walk(value):
                    if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                            and child.func.id == "exec"):
                        state.clear()
                    if isinstance(child, ast.NamedExpr):
                        state[child.target.id] = None
        elif isinstance(stmt, ast.Delete):
            # Deleting a name removes its earlier alias binding. For
            # attribute/subscript deletion, arbitrary user code may run.
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    state[target.id] = None
                else:
                    state.clear()
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
            # The RHS is evaluated too: a walrus may rebind another alias,
            # not just the augmented-assignment target.
            for child in ast.walk(stmt.value):
                if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                        and child.func.id == "exec"):
                    state.clear()
                if isinstance(child, ast.NamedExpr):
                    state[child.target.id] = None
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
                    if (isinstance(nested, ast.Call) and isinstance(nested.func, ast.Name)
                            and nested.func.id == "exec"):
                        state.clear()
                    if isinstance(nested, ast.NamedExpr):
                        state[nested.target.id] = None
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
            _scan_class_creation_expressions(
                list(stmt.decorator_list) + list(stmt.bases)
                + [kw.value for kw in stmt.keywords], state, findings,
                module_scope=True)
            # Class body statements execute during class creation, unlike
            # ordinary method bodies. Inspect only direct class-body calls.
            pending_classes = [stmt]
            while pending_classes:
                current_class = pending_classes.pop()
                local_lambdas = {}
                conditional_members = set()
                pending_members = list(current_class.body)
                while pending_members:
                    member = pending_members.pop(0)
                    # Nested control-flow suites execute during class creation;
                    # inspect their statements but never descend into deferred
                    # method bodies or lambda scopes.
                    if isinstance(member, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                           ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.Match)):
                        suites = []
                        for field, value in ast.iter_fields(member):
                            if field in ('body', 'orelse', 'finalbody') and isinstance(value, list):
                                suites.extend(value)
                            elif field == 'handlers' and isinstance(value, list):
                                for handler in value:
                                    suites.extend(handler.body)
                            elif field == 'cases' and isinstance(value, list):
                                for case in value:
                                    suites.extend(case.body)
                        # Flattening a conditional suite does not prove that
                        # its assignments execute on every runtime path.
                        conditional_members.update(id(item) for item in suites)
                        pending_members[0:0] = suites
                        # Expressions in the control-flow header can execute too.
                        header_expressions = []
                        if isinstance(member, (ast.If, ast.While)):
                            header_expressions = [member.test]
                        elif isinstance(member, (ast.For, ast.AsyncFor)):
                            header_expressions = [member.iter]
                        elif isinstance(member, (ast.With, ast.AsyncWith)):
                            header_expressions = [item.context_expr for item in member.items]
                        elif isinstance(member, ast.Match):
                            header_expressions = [member.subject]
                            header_expressions.extend(case.guard for case in member.cases
                                                      if case.guard is not None)
                        elif isinstance(member, (ast.Try, ast.TryStar)):
                            header_expressions = [handler.type for handler in member.handlers
                                                  if handler.type is not None]
                        _scan_class_creation_expressions(header_expressions, state, findings,
                                                     local_lambdas=local_lambdas)
                    # A global declaration can occur inside class-body control
                    # flow. Skip nested function/class scopes, which have their
                    # own declarations; nested classes are processed separately.
                    pending_globals = [member]
                    while pending_globals:
                        node = pending_globals.pop()
                        if isinstance(node, ast.Global):
                            for name in node.names:
                                state[name] = None
                        elif not isinstance(node, (ast.FunctionDef,
                                                   ast.AsyncFunctionDef,
                                                   ast.Lambda, ast.ClassDef)):
                            pending_globals.extend(ast.iter_child_nodes(node))
                    if isinstance(member, ast.ClassDef):
                        pending_classes.append(member)
                    if isinstance(member, ast.Expr):
                        expressions = [member.value]
                    elif isinstance(member, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                        expressions = [member.value] if member.value is not None else []
                        if isinstance(member, ast.AnnAssign):
                            expressions.append(member.annotation)
                    elif isinstance(member, ast.Assert):
                        expressions = [member.test] + ([member.msg] if member.msg is not None else [])
                    elif isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Method body is deferred; decorators and defaults
                        # execute while its enclosing class is created.
                        expressions = (list(member.decorator_list)
                                       + list(member.args.defaults)
                                       + [v for v in member.args.kw_defaults if v is not None]
                                       + [arg.annotation for arg in (
                                           member.args.posonlyargs + member.args.args
                                           + member.args.kwonlyargs
                                           + ([member.args.vararg] if member.args.vararg else [])
                                           + ([member.args.kwarg] if member.args.kwarg else []))
                                          if arg.annotation is not None]
                                       + ([member.returns] if member.returns is not None else []))
                    elif isinstance(member, ast.ClassDef):
                        expressions = (list(member.decorator_list) + list(member.bases)
                                       + [kw.value for kw in member.keywords])
                    else:
                        expressions = []
                    _scan_class_creation_expressions(expressions, state, findings,
                                                     local_lambdas=local_lambdas)
                    # Conditional rebinding cannot discard a callable that
                    # may still execute on another runtime path. Fail closed
                    # rather than treating the flattened suite as guaranteed.
                    if id(member) in conditional_members:
                        if isinstance(member, (ast.Assign, ast.AnnAssign,
                                               ast.AugAssign, ast.Delete)):
                            state.clear()
                        continue
                    # Only track simple, ordered class-local lambda bindings.
                    # Any other assignment invalidates the tracked callable.
                    if isinstance(member, ast.Assign):
                        for target in member.targets:
                            if isinstance(target, ast.Name):
                                if isinstance(member.value, ast.Lambda):
                                    local_lambdas[target.id] = member.value
                                else:
                                    local_lambdas.pop(target.id, None)
                    elif isinstance(member, (ast.AnnAssign, ast.AugAssign)):
                        if isinstance(member.target, ast.Name):
                            local_lambdas.pop(member.target.id, None)
                    elif isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef,
                                             ast.ClassDef)):
                        local_lambdas.pop(member.name, None)
        elif isinstance(stmt, ast.Assert):
            # Both the condition and optional message may evaluate bindings;
            # the message is conditional, so alias proof must stay conservative.
            for expression in (stmt.test, stmt.msg):
                if expression is None:
                    continue
                for child in ast.walk(expression):
                    if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                            and child.func.id == "exec"):
                        state.clear()
                    if isinstance(child, ast.NamedExpr):
                        state[child.target.id] = None
                    if isinstance(child, ast.Call):
                        findings.append({"line": child.lineno, "target": None,
                                         "classification": "uncertain_expression_call"})
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            # Direct exec can replace module globals dynamically. Without
            # proving its runtime namespace, no earlier alias stays proven.
            if (isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "exec"):
                state.clear()
            # The outer call is classified below; its nested arguments and
            # callable expression are inventoried separately as uncertain.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.Call) and child is not stmt.value:
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
            # The outer callable is looked up before its arguments. Resolve
            # that callable now, then invalidate aliases affected by nested
            # exec before analyzing any subsequent statement.
            nested_exec = any(
                isinstance(child, ast.Call)
                and child is not stmt.value
                and isinstance(child.func, ast.Name)
                and child.func.id == "exec"
                for child in ast.walk(stmt.value))
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
            # A walrus inside the arguments runs after the outer callable
            # has been resolved. Invalidate those names for later statements.
            for child in ast.walk(stmt.value):
                if isinstance(child, ast.NamedExpr):
                    state[child.target.id] = None
            if nested_exec:
                state.clear()
        elif isinstance(stmt, ast.Expr):
            # Non-call expressions may still bind names via walrus operators,
            # e.g. a conditional expression or an f-string. Invalidate these
            # bindings without attributing the calls inside the expression.
            # An embedded direct exec call can also replace module bindings.
            for child in ast.walk(stmt.value):
                if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                        and child.func.id == "exec"):
                    state.clear()
                if isinstance(child, ast.NamedExpr):
                    state[child.target.id] = None
                if isinstance(child, ast.Call):
                    findings.append({"line": child.lineno, "target": None,
                                     "classification": "uncertain_expression_call"})
    return findings
