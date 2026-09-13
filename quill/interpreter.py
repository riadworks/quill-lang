from quill import ast_nodes as A
from quill.environment import Environment
from quill.errors import RuntimeErr
from quill.values import BuiltinFunction, QuillFunction, is_truthy, quill_equals, quill_str, type_name


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
        env.declare(stmt.name, value)

    def exec_AssignStmt(self, stmt: A.AssignStmt, env):
        value = self.evaluate(stmt.expr, env)
        target = stmt.target
        if isinstance(target, A.NameExpr):
            env.assign(target.name, value, stmt.line)
        elif isinstance(target, A.Index):
            container = self.evaluate(target.obj, env)
            index = self.evaluate(target.index, env)
            self._set_index(container, index, value, stmt.line)
        else:
            raise RuntimeErr("invalid assignment target", stmt.line)

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
        for item in items:
            loop_env = Environment(env)
            loop_env.declare(stmt.var_name, item)
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

    def eval_NameExpr(self, expr: A.NameExpr, env):
        return env.get(expr.name, expr.line)

    def eval_Unary(self, expr: A.Unary, env):
        value = self.evaluate(expr.operand, env)
        if expr.op == "-":
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

        if op in ("-", "*", "/", "%", "**", "<", ">", "<=", ">="):
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
        return QuillFunction(expr.name, expr.params, expr.body, env)

    # ---------- calling / indexing helpers ----------

    def call(self, callee, args, line):
        if isinstance(callee, BuiltinFunction):
            return callee.fn(args, line)
        if isinstance(callee, QuillFunction):
            if len(args) != len(callee.params):
                raise RuntimeErr(
                    f"'{callee.name or 'anonymous'}' expects {len(callee.params)} argument(s), got {len(args)}", line
                )
            call_env = Environment(callee.closure)
            for name, value in zip(callee.params, args):
                call_env.declare(name, value)
            try:
                self._exec_block(callee.body, call_env)
            except ReturnSignal as r:
                return r.value
            return None
        raise RuntimeErr(f"'{type_name(callee)}' is not callable", line)

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
