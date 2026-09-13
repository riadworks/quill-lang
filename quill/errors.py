class QuillError(Exception):
    """Base for all errors that should be reported to the user nicely (not a Python traceback)."""

    def __init__(self, message: str, line: int = None):
        self.message = message
        self.line = line
        location = f" (line {line})" if line is not None else ""
        super().__init__(f"{message}{location}")


class LexError(QuillError):
    pass


class ParseError(QuillError):
    pass


class RuntimeErr(QuillError):
    pass


class QuillThrow(QuillError):
    """A user `raise expr` - carries an arbitrary Quill value, catchable by try/except.

    Subclasses QuillError (rather than plain Exception) so that an uncaught raise -
    one with no matching try/except - is still handled by the same top-level error
    reporting as every other kind of error, instead of crashing the CLI/REPL with a
    raw Python traceback.
    """

    def __init__(self, value, line=None):
        from quill.values import quill_str

        self.value = value
        super().__init__(quill_str(value), line)
