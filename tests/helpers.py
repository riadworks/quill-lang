import contextlib
import io

from quill.builtins import build_globals
from quill.errors import QuillError
from quill.interpreter import Interpreter
from quill.lexer import tokenize
from quill.parser import parse


def run(source: str) -> str:
    """Run source, return everything it printed to stdout."""
    env = build_globals()
    interp = Interpreter(env)
    tokens = tokenize(source)
    program = parse(tokens)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(program)
    return buf.getvalue()


def run_expect_error(source: str) -> str:
    """Run source, expect a QuillError, return its message."""
    env = build_globals()
    interp = Interpreter(env)
    tokens = tokenize(source)
    program = parse(tokens)
    try:
        interp.run(program)
    except QuillError as exc:
        return str(exc)
    raise AssertionError("expected a QuillError but none was raised")
