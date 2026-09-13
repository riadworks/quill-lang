from quill.errors import LexError
from quill.tokens import KEYWORDS, T, Token

SINGLE_CHAR = {
    "%": T.PERCENT,
    "(": T.LPAREN,
    ")": T.RPAREN,
    "[": T.LBRACKET,
    "]": T.RBRACKET,
    "{": T.LBRACE,
    "}": T.RBRACE,
    ",": T.COMMA,
    ":": T.COLON,
    ".": T.DOT,
}


class Lexer:
    def __init__(self, source: str):
        # strip a leading UTF-8 BOM (common from Windows editors/tools) and normalize line endings
        if source.startswith("﻿"):
            source = source[1:]
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent_stack = [0]
        self.paren_depth = 0
        self.at_line_start = True
        self.tokens: list[Token] = []

    def error(self, msg):
        raise LexError(msg, self.line)

    def peek(self, offset=0):
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.src):
            if self.at_line_start and self.paren_depth == 0:
                if not self._handle_indentation():
                    continue
            self._scan_token()

        # close out any dangling logical line, then dedent everything
        if self.tokens and self.tokens[-1].type != T.NEWLINE:
            self.tokens.append(Token(T.NEWLINE, None, self.line, self.col))
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(T.DEDENT, None, self.line, self.col))
        self.tokens.append(Token(T.EOF, None, self.line, self.col))
        return self.tokens

    def _handle_indentation(self) -> bool:
        """Measure leading whitespace of a new logical line. Returns False if the whole
        line was blank/comment-only (caller should loop again), True once real content
        starts and INDENT/DEDENT tokens (if any) have been emitted."""
        start = self.pos
        width = 0
        while self.peek() in (" ", "\t"):
            width += 8 - (width % 8) if self.peek() == "\t" else 1
            self.advance()

        if self.peek() in ("\n", "", "#"):
            # blank line or comment-only line: skip it, doesn't affect indentation
            if self.peek() == "#":
                while self.peek() not in ("\n", ""):
                    self.advance()
            if self.peek() == "\n":
                self.advance()
            return False

        self.at_line_start = False
        current = self.indent_stack[-1]
        if width > current:
            self.indent_stack.append(width)
            self.tokens.append(Token(T.INDENT, width, self.line, 1))
        elif width < current:
            while self.indent_stack[-1] > width:
                self.indent_stack.pop()
                self.tokens.append(Token(T.DEDENT, None, self.line, 1))
            if self.indent_stack[-1] != width:
                self.error("inconsistent indentation")
        return True

    def _scan_token(self):
        ch = self.peek()

        if ch == "":
            return

        if ch == "\n":
            self.advance()
            if self.paren_depth == 0:
                if self.tokens and self.tokens[-1].type != T.NEWLINE:
                    self.tokens.append(Token(T.NEWLINE, None, self.line - 1, self.col))
                self.at_line_start = True
            return

        if ch in (" ", "\t"):
            self.advance()
            return

        if ch == "#":
            while self.peek() not in ("\n", ""):
                self.advance()
            return

        line, col = self.line, self.col

        if ch == '"':
            self._scan_string(line, col, interpolate=False)
            return

        if ch.isdigit():
            self._scan_number(line, col)
            return

        if ch.isalpha() or ch == "_":
            self._scan_name(line, col)
            return

        if ch in "([{":
            self.paren_depth += 1
        elif ch in ")]}":
            self.paren_depth = max(0, self.paren_depth - 1)

        if ch in SINGLE_CHAR:
            self.advance()
            self.tokens.append(Token(SINGLE_CHAR[ch], ch, line, col))
            return

        if ch == "+":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.PLUSEQ, "+=", line, col))
            else:
                self.tokens.append(Token(T.PLUS, "+", line, col))
            return

        if ch == "-":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.MINUSEQ, "-=", line, col))
            else:
                self.tokens.append(Token(T.MINUS, "-", line, col))
            return

        if ch == "*":
            self.advance()
            if self.peek() == "*":
                self.advance()
                self.tokens.append(Token(T.STARSTAR, "**", line, col))
            elif self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.STAREQ, "*=", line, col))
            else:
                self.tokens.append(Token(T.STAR, "*", line, col))
            return

        if ch == "/":
            self.advance()
            if self.peek() == "/":
                self.advance()
                self.tokens.append(Token(T.SLASHSLASH, "//", line, col))
            elif self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.SLASHEQ, "/=", line, col))
            else:
                self.tokens.append(Token(T.SLASH, "/", line, col))
            return

        if ch == "=":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.EQEQ, "==", line, col))
            else:
                self.tokens.append(Token(T.EQ, "=", line, col))
            return

        if ch == "!":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.NEQ, "!=", line, col))
            else:
                self.error(f"unexpected character '!'")
            return

        if ch == "<":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.LE, "<=", line, col))
            else:
                self.tokens.append(Token(T.LT, "<", line, col))
            return

        if ch == ">":
            self.advance()
            if self.peek() == "=":
                self.advance()
                self.tokens.append(Token(T.GE, ">=", line, col))
            else:
                self.tokens.append(Token(T.GT, ">", line, col))
            return

        self.error(f"unexpected character {ch!r}")

    def _scan_string(self, line, col, interpolate: bool):
        self.advance()  # opening quote
        parts = []  # list of ("lit", str) or ("expr", str) pieces for interpolation
        buf = []
        while True:
            c = self.peek()
            if c == "":
                self.error("unterminated string")
            if c == '"':
                self.advance()
                break
            if c == "\\":
                self.advance()
                esc = self.advance()
                buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\", "{": "{"}.get(esc, esc))
                continue
            if c == "{" and interpolate:
                parts.append(("lit", "".join(buf)))
                buf = []
                self.advance()
                depth = 1
                expr_chars = []
                while True:
                    c2 = self.peek()
                    if c2 == "":
                        self.error("unterminated interpolation")
                    if c2 == "{":
                        depth += 1
                    elif c2 == "}":
                        depth -= 1
                        if depth == 0:
                            self.advance()
                            break
                    expr_chars.append(self.advance())
                parts.append(("expr", "".join(expr_chars)))
                continue
            buf.append(self.advance())
        parts.append(("lit", "".join(buf)))
        self.tokens.append(Token(T.STRING, parts, line, col))

    def _scan_number(self, line, col):
        start = self.pos
        while self.peek().isdigit():
            self.advance()
        is_float = False
        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            self.advance()
            while self.peek().isdigit():
                self.advance()
        if self.peek() in ("e", "E"):
            is_float = True
            self.advance()
            if self.peek() in ("+", "-"):
                self.advance()
            while self.peek().isdigit():
                self.advance()
        text = self.src[start:self.pos]
        value = float(text) if is_float else int(text)
        self.tokens.append(Token(T.NUMBER, value, line, col))

    def _scan_name(self, line, col):
        start = self.pos
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        text = self.src[start:self.pos]

        if text == "f" and self.peek() == '"':
            self._scan_string(line, col, interpolate=True)
            return

        kind = KEYWORDS.get(text)
        if kind is not None:
            self.tokens.append(Token(kind, text, line, col))
        else:
            self.tokens.append(Token(T.NAME, text, line, col))


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
