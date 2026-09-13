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
