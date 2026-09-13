from enum import Enum, auto


class T(Enum):
    # literals
    NUMBER = auto()
    STRING = auto()
    NAME = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()

    # keywords
    LET = auto()
    FN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    CLASS = auto()
    SELF = auto()
    SUPER = auto()
    TRY = auto()
    EXCEPT = auto()
    FINALLY = auto()
    RAISE = auto()
    IMPORT = auto()
    AS = auto()

    # operators / punctuation
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    STARSTAR = auto()
    SLASHSLASH = auto()
    PLUSEQ = auto()
    MINUSEQ = auto()
    STAREQ = auto()
    SLASHEQ = auto()
    EQ = auto()
    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()

    # structural
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "let": T.LET,
    "fn": T.FN,
    "if": T.IF,
    "elif": T.ELIF,
    "else": T.ELSE,
    "while": T.WHILE,
    "for": T.FOR,
    "in": T.IN,
    "return": T.RETURN,
    "break": T.BREAK,
    "continue": T.CONTINUE,
    "and": T.AND,
    "or": T.OR,
    "not": T.NOT,
    "true": T.TRUE,
    "false": T.FALSE,
    "nil": T.NIL,
    "class": T.CLASS,
    "self": T.SELF,
    "super": T.SUPER,
    "try": T.TRY,
    "except": T.EXCEPT,
    "finally": T.FINALLY,
    "raise": T.RAISE,
    "import": T.IMPORT,
    "as": T.AS,
}


class Token:
    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_: T, value, line: int, col: int):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"
