from quill import ast_nodes as A
from quill.environment import Environment
from quill.errors import QuillThrow, RuntimeErr
from quill.values import (
    BoundBuiltinMethod,
    BoundInstanceMethod,
    BuiltinFunction,
    QuillClass,
    QuillFunction,
    QuillInstance,
    SuperProxy,
    is_truthy,
    quill_equals,
    quill_str,
    type_name,
)

# The single currently-running Interpreter, so builtin higher-order functions
# (map/filter/reduce in methods.py) can call back into user-defined functions
# without methods.py needing to import interpreter.py at module load time.
CURRENT_INTERPRETER = [None]

# Operator overloading: a class defining one of these methods has it called for the
# matching operator when the left-hand operand is an instance of that class. Matches
# Python's dunder-method convention so it's immediately familiar. No reflected
# (__radd__-style) operators in v1 - the overload only fires when the instance is
# the left operand.
BINARY_DUNDERS = {
    "+": "__add__",
    "-": "__sub__",
    "*": "__mul__",
    "/": "__div__",
    "//": "__floordiv__",
    "%": "__mod__",
    "**": "__pow__",
    "<": "__lt__",
    ">": "__gt__",
    "<=": "__le__",
    ">=": "__ge__",
    "==": "__eq__",
    "!=": "__eq__",
}

# Comparison dunders always coerce their result to a real boolean (like != already
# did) so a sloppy __eq__/__lt__ implementation that returns something non-boolean
# still prints as true/false rather than leaking a raw value out through == or <.
# Arithmetic dunders (__add__ etc.) are exempt - their whole point is returning a
# new instance, not a boolean.
COMPARISON_OPS = {"==", "!=", "<", ">", "<=", ">="}


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Interpreter:
    def __init__(self, globals_env: Environment):
        self.globals = globals_env
        CURRENT_INTERPRETER[0] = self

    def run(self, program: list):
        for stmt in program:
            self.execute(stmt, self.globals)

    # ---------- statements ----------

    def execute(self, stmt, env: Environment):
        method = getattr(self, f"exec_{type(stmt).__name__}", None)
        if method is None:
            raise RuntimeErr(f"internal error: no executor for {type(stmt).__name__}", getattr(stmt, "line", None))
        method(stmt, env)

    def exec_ExprStmt(self, stmt: A.ExprStmt, env):
        self.evaluate(stmt.expr, env)

    def exec_LetStmt(self, stmt: A.LetStmt, env):
        value = self.evaluate(stmt.expr, env)
        if len(stmt.names) == 1:
            env.declare(stmt.names[0], value)
        else:
            for name, item in self._unpack(stmt.names, value, stmt.line):
                env.declare(name, item)

    def exec_UnpackAssignStmt(self, stmt: A.UnpackAssignStmt, env):
        value = self.evaluate(stmt.expr, env)
        for name, item in self._unpack(stmt.names, value, stmt.line):
            env.assign(name, item, stmt.line)

    def _unpack(self, names, value, line):
        """Shared by `let a, b = ...` and bare `a, b = ...` - splits a list value
        into (name, item) pairs, matching Python's "too many/few values to
        unpack" behavior instead of silently truncating or padding with nil."""
        if not isinstance(value, list):
            raise RuntimeErr(f"cannot unpack a {type_name(value)} into {len(names)} names", line)
        if len(value) != len(names):
            raise RuntimeErr(
                f"too {'many' if len(value) > len(names) else 'few'} values to unpack "
                f"(expected {len(names)}, got {len(value)})",
                line,
            )
        return list(zip(names, value))

    def exec_AssignStmt(self, stmt: A.AssignStmt, env):
        value = self.evaluate(stmt.expr, env)
        target = stmt.target
        if isinstance(target, A.NameExpr):
            env.assign(target.name, value, stmt.line)
        elif isinstance(target, A.Index):
            container = self.evaluate(target.obj, env)
            index = self.evaluate(target.index, env)
            self._set_index(container, index, value, stmt.line)
        elif isinstance(target, A.Get):
            obj = self.evaluate(target.obj, env)
            if isinstance(obj, QuillInstance):
                obj.fields[target.name] = value
            elif isinstance(obj, dict):
                obj[target.name] = value
            else:
                raise RuntimeErr(f"cannot assign to '.{target.name}' on a {type_name(obj)}", stmt.line)
        else:
            raise RuntimeErr("invalid assignment target", stmt.line)

    def exec_ClassDecl(self, stmt: A.ClassDecl, env):
        superclass = None
        if stmt.superclass_name is not None:
            superclass = env.get(stmt.superclass_name, stmt.line)
            if not isinstance(superclass, QuillClass):
                raise RuntimeErr(f"'{stmt.superclass_name}' is not a class", stmt.line)
        quill_class = QuillClass(stmt.name, {}, superclass)
        quill_class.methods = {
            name: QuillFunction(name, fn_expr.params, fn_expr.defaults, fn_expr.body, env, owner_class=quill_class)
            for name, fn_expr in stmt.methods.items()
        }
        env.declare(stmt.name, quill_class)

    def exec_TryStmt(self, stmt: A.TryStmt, env):
        try:
            try:
                self._exec_block(stmt.body, Environment(env))
            except QuillThrow as thrown:
                if stmt.except_body is None:
                    raise
                self._run_except(stmt, thrown.value, env)
            except RuntimeErr as err:
                if stmt.except_body is None:
                    raise
                self._run_except(stmt, err.message, env)
        finally:
            if stmt.finally_body is not None:
                self._exec_block(stmt.finally_body, Environment(env))

    def _run_except(self, stmt: A.TryStmt, value, env):
        handler_env = Environment(env)
        if stmt.except_name is not None:
            handler_env.declare(stmt.except_name, value)
        self._exec_block(stmt.except_body, handler_env)

    def exec_RaiseStmt(self, stmt: A.RaiseStmt, env):
        value = self.evaluate(stmt.expr, env)
        raise QuillThrow(value, stmt.line)

    def exec_ImportStmt(self, stmt: A.ImportStmt, env):
        import os

        from quill.builtins import build_globals
        from quill.lexer import tokenize
        from quill.parser import parse

        base_dir = getattr(self, "current_dir", ".")
        full_path = os.path.join(base_dir, stmt.path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as exc:
            raise RuntimeErr(f"cannot import '{stmt.path}': {exc.strerror}", stmt.line)

        module_env = build_globals()
        module_interp = Interpreter(module_env)
        module_interp.current_dir = os.path.dirname(full_path) or "."
        program = parse(tokenize(source))
        module_interp.run(program)
        CURRENT_INTERPRETER[0] = self  # restore - imports may nest/finish out of order otherwise

        namespace = dict(module_env.vars)
        env.declare(stmt.alias, namespace)

    def exec_IfStmt(self, stmt: A.IfStmt, env):
        for cond, body in stmt.branches:
            if is_truthy(self.evaluate(cond, env)):
                self._exec_block(body, Environment(env))
                return
        if stmt.else_body is not None:
            self._exec_block(stmt.else_body, Environment(env))

    def exec_WhileStmt(self, stmt: A.WhileStmt, env):
        while is_truthy(self.evaluate(stmt.cond, env)):
            try:
                self._exec_block(stmt.body, Environment(env))
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def exec_ForStmt(self, stmt: A.ForStmt, env):
        iterable = self.evaluate(stmt.iterable, env)
        items = self._to_iterable(iterable, stmt.line)
        single = len(stmt.var_names) == 1
        for item in items:
            loop_env = Environment(env)
            if single:
                loop_env.declare(stmt.var_names[0], item)
            else:
                for name, value in self._unpack(stmt.var_names, item, stmt.line):
                    loop_env.declare(name, value)
            try:
                self._exec_block(stmt.body, loop_env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def exec_ReturnStmt(self, stmt: A.ReturnStmt, env):
        value = self.evaluate(stmt.expr, env) if stmt.expr is not None else None
        raise ReturnSignal(value)

    def exec_BreakStmt(self, stmt: A.BreakStmt, env):
        raise BreakSignal()

    def exec_ContinueStmt(self, stmt: A.ContinueStmt, env):
        raise ContinueSignal()

    def _exec_block(self, stmts, env):
        for stmt in stmts:
            self.execute(stmt, env)

    def _to_iterable(self, value, line):
        if isinstance(value, list):
            return list(value)
        if isinstance(value, str):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        raise RuntimeErr(f"cannot iterate over a {type_name(value)}", line)

    # ---------- expressions ----------

    def evaluate(self, expr, env: Environment):
        method = getattr(self, f"eval_{type(expr).__name__}", None)
        if method is None:
            raise RuntimeErr(f"internal error: no evaluator for {type(expr).__name__}", getattr(expr, "line", None))
        return method(expr, env)

    def eval_NumberLit(self, expr: A.NumberLit, env):
        return expr.value

    def eval_BoolLit(self, expr: A.BoolLit, env):
        return expr.value

    def eval_NilLit(self, expr: A.NilLit, env):
        return None

    def eval_StringLit(self, expr: A.StringLit, env):
        out = []
        for kind, part in expr.parts:
            if kind == "lit":
                out.append(part)
            else:
                out.append(quill_str(self.evaluate(part, env)))
        return "".join(out)

    def eval_ListLit(self, expr: A.ListLit, env):
        return [self.evaluate(e, env) for e in expr.elements]

    def eval_MapLit(self, expr: A.MapLit, env):
        result = {}
        for key_expr, value_expr in expr.pairs:
            key = self.evaluate(key_expr, env)
            if not isinstance(key, (str, int, float, bool)):
                raise RuntimeErr(f"map keys must be a string, number, or bool, not {type_name(key)}", expr.line)
            result[key] = self.evaluate(value_expr, env)
        return result

    def _run_comprehension(self, clauses, index, env, on_match):
        """Recursively binds each clause's loop variable (checking its own filter
        condition right after binding, like nested for-loops), calling on_match(env)
        once per combination that satisfies every clause - supports chained
        `for x in a for y in b if ...` the same way Python's comprehensions do."""
        if index == len(clauses):
            on_match(env)
            return
        clause = clauses[index]
        iterable = self.evaluate(clause.iterable, env)
        items = self._to_iterable(iterable, clause.line)
        for item in items:
            child_env = Environment(env)
            child_env.declare(clause.var_name, item)
            if clause.condition is not None and not is_truthy(self.evaluate(clause.condition, child_env)):
                continue
            self._run_comprehension(clauses, index + 1, child_env, on_match)

    def eval_ListComp(self, expr: A.ListComp, env):
        result = []
        self._run_comprehension(expr.clauses, 0, env, lambda e: result.append(self.evaluate(expr.expr, e)))
        return result

    def eval_MapComp(self, expr: A.MapComp, env):
        result = {}

        def collect(final_env):
            key = self.evaluate(expr.key_expr, final_env)
            if not isinstance(key, (str, int, float, bool)):
                raise RuntimeErr(f"map keys must be a string, number, or bool, not {type_name(key)}", expr.line)
            result[key] = self.evaluate(expr.value_expr, final_env)

        self._run_comprehension(expr.clauses, 0, env, collect)
        return result

    def eval_NameExpr(self, expr: A.NameExpr, env):
        return env.get(expr.name, expr.line)

    def eval_Unary(self, expr: A.Unary, env):
        value = self.evaluate(expr.operand, env)
        if expr.op == "-":
            if isinstance(value, QuillInstance):
                method = value.klass.find_method("__neg__")
                if method is not None:
                    return self._call_quill_function(method, [], expr.line, self_instance=value)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise RuntimeErr(f"cannot negate a {type_name(value)}", expr.line)
            return -value
        if expr.op == "not":
            return not is_truthy(value)
        raise RuntimeErr(f"internal error: unknown unary operator {expr.op}", expr.line)

    def eval_Logical(self, expr: A.Logical, env):
        left = self.evaluate(expr.left, env)
        if expr.op == "and":
            return self.evaluate(expr.right, env) if is_truthy(left) else left
        if expr.op == "or":
            return left if is_truthy(left) else self.evaluate(expr.right, env)
        raise RuntimeErr(f"internal error: unknown logical operator {expr.op}", expr.line)

    def eval_Binary(self, expr: A.Binary, env):
        left = self.evaluate(expr.left, env)
        right = self.evaluate(expr.right, env)
        op = expr.op
        line = expr.line

        if isinstance(left, QuillInstance):
            dunder = BINARY_DUNDERS.get(op)
            method = left.klass.find_method(dunder) if dunder else None
            if method is not None:
                result = self._call_quill_function(method, [right], line, self_instance=left)
                if op in COMPARISON_OPS:
                    truthy = is_truthy(result)
                    return not truthy if op == "!=" else truthy
                return result

        if op == "==":
            return quill_equals(left, right)
        if op == "!=":
            return not quill_equals(left, right)

        if op == "+":
            if _is_num(left) and _is_num(right):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            raise RuntimeErr(
                f"cannot add {type_name(left)} and {type_name(right)} (use str() to convert first)", line
            )

        if op in ("-", "*", "/", "//", "%", "**", "<", ">", "<=", ">="):
            if not (_is_num(left) and _is_num(right)):
                raise RuntimeErr(f"cannot use '{op}' on {type_name(left)} and {type_name(right)}", line)
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise RuntimeErr("division by zero", line)
                return left / right
            if op == "//":
                if right == 0:
                    raise RuntimeErr("division by zero", line)
                return left // right
            if op == "%":
                if right == 0:
                    raise RuntimeErr("division by zero", line)
                return left % right
            if op == "**":
                return left**right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right

        raise RuntimeErr(f"internal error: unknown operator {op}", line)

    def eval_Index(self, expr: A.Index, env):
        obj = self.evaluate(expr.obj, env)
        index = self.evaluate(expr.index, env)
        return self._get_index(obj, index, expr.line)

    def eval_Call(self, expr: A.Call, env):
        callee = self.evaluate(expr.callee, env)
        args = [self.evaluate(a, env) for a in expr.args]
        return self.call(callee, args, expr.line)

    def eval_FnExpr(self, expr: A.FnExpr, env):
        return QuillFunction(expr.name, expr.params, expr.defaults, expr.body, env)

    def eval_Ternary(self, expr: A.Ternary, env):
        if is_truthy(self.evaluate(expr.cond, env)):
            return self.evaluate(expr.then_expr, env)
        return self.evaluate(expr.else_expr, env)

    def eval_Get(self, expr: A.Get, env):
        obj = self.evaluate(expr.obj, env)
        return self._get_attr(obj, expr.name, expr.line)

    def eval_SuperExpr(self, expr: A.SuperExpr, env):
        self_instance = env.get("self", expr.line)
        superclass = env.get("__super_class__", expr.line)
        if superclass is None:
            raise RuntimeErr("'super' used outside of a subclass method", expr.line)
        return SuperProxy(self_instance, superclass)

    def _get_attr(self, obj, name, line):
        if isinstance(obj, QuillInstance):
            if name in obj.fields:
                return obj.fields[name]
            method = obj.klass.find_method(name)
            if method is not None:
                return BoundInstanceMethod(obj, method)
            raise RuntimeErr(f"'{obj.klass.name}' has no field or method '{name}'", line)
        if isinstance(obj, SuperProxy):
            method = obj.superclass.find_method(name)
            if method is None:
                raise RuntimeErr(f"'{obj.superclass.name}' has no method '{name}'", line)
            return BoundInstanceMethod(obj.instance, method)
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
            from quill.methods import MAP_METHODS

            if name in MAP_METHODS:
                return BoundBuiltinMethod(obj, name, MAP_METHODS[name])
            raise RuntimeErr(f"map has no key or method '{name}'", line)
        if isinstance(obj, list):
            from quill.methods import LIST_METHODS

            if name in LIST_METHODS:
                return BoundBuiltinMethod(obj, name, LIST_METHODS[name])
            raise RuntimeErr(f"list has no method '{name}'", line)
        if isinstance(obj, str):
            from quill.methods import STRING_METHODS

            if name in STRING_METHODS:
                return BoundBuiltinMethod(obj, name, STRING_METHODS[name])
            raise RuntimeErr(f"string has no method '{name}'", line)
        raise RuntimeErr(f"cannot access '.{name}' on a {type_name(obj)}", line)

    # ---------- calling / indexing helpers ----------

    def call(self, callee, args, line):
        if isinstance(callee, BuiltinFunction):
            return callee.fn(args, line)

        if isinstance(callee, BoundBuiltinMethod):
            return callee.fn(callee.receiver, args, line)

        if isinstance(callee, BoundInstanceMethod):
            return self._call_quill_function(callee.func, args, line, self_instance=callee.instance)

        if isinstance(callee, QuillClass):
            instance = QuillInstance(callee)
            init_method = callee.find_method("init")
            if init_method is not None:
                self._call_quill_function(init_method, args, line, self_instance=instance)
            elif args:
                raise RuntimeErr(f"'{callee.name}' has no init() but {len(args)} argument(s) were given", line)
            return instance

        if isinstance(callee, QuillFunction):
            return self._call_quill_function(callee, args, line)

        raise RuntimeErr(f"'{type_name(callee)}' is not callable", line)

    def _call_quill_function(self, fn: QuillFunction, args, line, self_instance=None):
        num_total = len(fn.params)
        num_required = sum(1 for d in fn.defaults if d is None)
        if not (num_required <= len(args) <= num_total):
            label = f"{num_total}" if num_required == num_total else f"{num_required}-{num_total}"
            raise RuntimeErr(f"'{fn.name or 'anonymous'}' expects {label} argument(s), got {len(args)}", line)
        call_env = Environment(fn.closure)
        if self_instance is not None:
            call_env.declare("self", self_instance)
            call_env.declare("__super_class__", fn.owner_class.superclass if fn.owner_class else None)
        # Defaults are evaluated here, in the call's own environment, rather than
        # once at definition time the way Python does it - so a default can refer
        # to an earlier parameter (`pull f(a, b=a*2):`), and there's no equivalent
        # of Python's classic mutable-default-argument bug, since nothing is
        # computed once and reused across calls.
        for i, name in enumerate(fn.params):
            if i < len(args):
                call_env.declare(name, args[i])
            else:
                call_env.declare(name, self.evaluate(fn.defaults[i], call_env))
        try:
            self._exec_block(fn.body, call_env)
        except ReturnSignal as r:
            return r.value
        return None

    def _get_index(self, obj, index, line):
        if isinstance(obj, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErr(f"list index must be a number, not {type_name(index)}", line)
            if index < 0:
                index += len(obj)
            if not (0 <= index < len(obj)):
                raise RuntimeErr(f"list index out of range", line)
            return obj[index]
        if isinstance(obj, dict):
            if index not in obj:
                raise RuntimeErr(f"key not found: {index!r}", line)
            return obj[index]
        if isinstance(obj, str):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErr(f"string index must be a number, not {type_name(index)}", line)
            if index < 0:
                index += len(obj)
            if not (0 <= index < len(obj)):
                raise RuntimeErr("string index out of range", line)
            return obj[index]
        raise RuntimeErr(f"cannot index into a {type_name(obj)}", line)

    def _set_index(self, obj, index, value, line):
        if isinstance(obj, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErr(f"list index must be a number, not {type_name(index)}", line)
            if index < 0:
                index += len(obj)
            if not (0 <= index < len(obj)):
                raise RuntimeErr("list index out of range", line)
            obj[index] = value
            return
        if isinstance(obj, dict):
            obj[index] = value
            return
        raise RuntimeErr(f"cannot assign into a {type_name(obj)}", line)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)
