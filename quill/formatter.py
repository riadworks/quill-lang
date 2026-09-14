"""A minimal source formatter: normalizes indentation to 4 spaces per level.

This deliberately does not rewrite spacing, operator style, or line breaks -
it only fixes the leading whitespace of each line that actually starts a new
logical statement. The reason is structural: Quill's lexer discards comments
entirely rather than keeping them as tokens (see lexer.py's `#` handling), so
a full AST-based pretty-printer would silently delete every comment in the
file when it re-emitted source from the tree. Working at the token-stream
level instead - using the real Lexer's own INDENT/DEDENT tracking to learn
each logical line's nesting depth, then rewriting only that line's leading
whitespace - fixes the single most common real formatting complaint
(inconsistent indentation, tabs vs. spaces) without ever touching a comment,
a string's contents, or anything after the first non-whitespace character.

A file with genuinely inconsistent indentation (mixing widths in a way the
lexer can't resolve into a consistent stack of levels) still fails to
tokenize at all - this normalizes *style*, it does not repair broken
structure.
"""

from quill.lexer import Lexer
from quill.tokens import T

INDENT_UNIT = "    "


def format_source(source: str) -> str:
    tokens = Lexer(source).tokenize()

    depth = 0
    line_depth = {}
    at_line_start = True
    for tok in tokens:
        if tok.type == T.INDENT:
            depth += 1
            at_line_start = True
            continue
        if tok.type == T.DEDENT:
            depth -= 1
            at_line_start = True
            continue
        if tok.type == T.NEWLINE:
            at_line_start = True
            continue
        if tok.type == T.EOF:
            continue
        if at_line_start:
            line_depth[tok.line] = depth
            at_line_start = False

    lines = source.splitlines(keepends=True)
    out = []
    for i, line in enumerate(lines, start=1):
        if i in line_depth:
            content = line.lstrip(" \t")
            out.append(INDENT_UNIT * line_depth[i] + content)
        else:
            out.append(line)
    return "".join(out)
