"""AST node definitions. Plain dataclasses - no behavior, just structure."""

from dataclasses import dataclass, field
from typing import Optional, Union


# ---------- Expressions ----------

@dataclass
class NumberLit:
    value: float
    line: int = 0


@dataclass
class StringLit:
    # parts: list of ("lit", str) or ("expr", <expr node>)
    parts: list
    line: int = 0


@dataclass
class BoolLit:
    value: bool
    line: int = 0


@dataclass
class NilLit:
    line: int = 0


@dataclass
class ListLit:
    elements: list
    line: int = 0


@dataclass
class MapLit:
    pairs: list  # list of (key_expr, value_expr)
    line: int = 0


@dataclass
class CompClause:
    var_name: str
    iterable: object
    condition: Optional[object] = None
    line: int = 0


@dataclass
class ListComp:
    expr: object
    clauses: list  # list of CompClause - supports [x*y for x in a for y in b if ...]
    line: int = 0


@dataclass
class MapComp:
    key_expr: object
    value_expr: object
    clauses: list
    line: int = 0


@dataclass
class NameExpr:
    name: str
    line: int = 0


@dataclass
class Unary:
    op: str
    operand: object
    line: int = 0


@dataclass
class Binary:
    op: str
    left: object
    right: object
    line: int = 0


@dataclass
class Logical:
    op: str  # "and" / "or"
    left: object
    right: object
    line: int = 0


@dataclass
class Call:
    callee: object
    args: list
    line: int = 0


@dataclass
class Index:
    obj: object
    index: object
    line: int = 0


@dataclass
class FnExpr:
    params: list
    defaults: list  # parallel to params: None for a required param, an expr node for a default
    body: list
    name: Optional[str] = None  # set for named `fn foo(...):` declarations, else None
    line: int = 0


@dataclass
class Get:
    obj: object
    name: str
    line: int = 0


@dataclass
class SuperExpr:
    line: int = 0


@dataclass
class Ternary:
    cond: object
    then_expr: object
    else_expr: object
    line: int = 0


# ---------- Statements ----------

@dataclass
class ExprStmt:
    expr: object
    line: int = 0


@dataclass
class LetStmt:
    names: list  # list[str] - length 1 for `let x = ...`, more for `let a, b = pair`
    expr: object
    line: int = 0


@dataclass
class AssignStmt:
    target: object  # NameExpr, Index, or Get
    expr: object
    line: int = 0


@dataclass
class UnpackAssignStmt:
    names: list  # list[str] - bare `a, b = pair` (reassigns existing names, no `let`)
    expr: object
    line: int = 0


@dataclass
class IfStmt:
    branches: list  # list of (cond_expr, body_stmts)
    else_body: Optional[list]
    line: int = 0


@dataclass
class WhileStmt:
    cond: object
    body: list
    line: int = 0


@dataclass
class ForStmt:
    var_names: list  # list[str] - length 1 for `for x in xs:`, more for `for k, v in pairs:`
    iterable: object
    body: list
    line: int = 0


@dataclass
class ReturnStmt:
    expr: Optional[object]
    line: int = 0


@dataclass
class BreakStmt:
    line: int = 0


@dataclass
class ContinueStmt:
    line: int = 0


@dataclass
class ClassDecl:
    name: str
    superclass_name: Optional[str]
    methods: dict  # name -> FnExpr
    line: int = 0


@dataclass
class TryStmt:
    body: list
    except_name: Optional[str]
    except_body: Optional[list]
    finally_body: Optional[list]
    line: int = 0


@dataclass
class RaiseStmt:
    expr: object
    line: int = 0


@dataclass
class ImportStmt:
    path: str
    alias: str
    line: int = 0
