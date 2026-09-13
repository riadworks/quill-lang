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
    body: list
    name: Optional[str] = None  # set for named `fn foo(...):` declarations, else None
    line: int = 0


# ---------- Statements ----------

@dataclass
class ExprStmt:
    expr: object
    line: int = 0


@dataclass
class LetStmt:
    name: str
    expr: object
    line: int = 0


@dataclass
class AssignStmt:
    target: object  # NameExpr or Index
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
    var_name: str
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
