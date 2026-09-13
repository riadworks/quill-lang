import os
import sys

from quill.builtins import build_globals
from quill.environment import Environment
from quill.errors import QuillError
from quill.interpreter import Interpreter
from quill.lexer import tokenize
from quill.parser import parse


def run_source(source: str, interp: Interpreter, env: Environment):
    tokens = tokenize(source)
    program = parse(tokens)
    interp.run(program)


def run_file(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    env = build_globals()
    interp = Interpreter(env)
    interp.current_dir = os.path.dirname(os.path.abspath(path))
    try:
        run_source(source, interp, env)
    except QuillError as exc:
        print(f"Error: {exc.message}" + (f" (line {exc.line})" if exc.line else ""), file=sys.stderr)
        return 1
    return 0


def repl() -> int:
    print("Quill REPL. Ctrl+D (or Ctrl+Z then Enter on Windows) to exit.")
    env = build_globals()
    interp = Interpreter(env)
    buffer = []
    while True:
        try:
            prompt = "... " if buffer else ">>> "
            line = input(prompt)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            buffer = []
            continue

        if line.strip() == "" and not buffer:
            continue

        buffer.append(line)
        # a very simple heuristic: keep reading while the line ends with ':' (starts a block)
        # or the buffer is still open (unbalanced brackets), otherwise try to run it.
        source = "\n".join(buffer)
        if line.rstrip().endswith(":") or _unbalanced(source):
            continue

        try:
            tokens = tokenize(source + "\n")
            program = parse(tokens)
            interp.run(program)
        except QuillError as exc:
            print(f"Error: {exc.message}" + (f" (line {exc.line})" if exc.line else ""))
        buffer = []


def _unbalanced(source: str) -> bool:
    depth = 0
    for ch in source:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
    return depth > 0


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        return repl()
    if argv[0] in ("-h", "--help"):
        print("usage: quill [script.ql]   (no script = start the REPL)")
        return 0
    return run_file(argv[0])


if __name__ == "__main__":
    sys.exit(main())
