"""Runtime value representations and formatting helpers.

Quill values map onto native Python types where possible: numbers -> int/float,
strings -> str, booleans -> bool, nil -> None, lists -> list, maps -> dict.
User-defined functions and built-ins get their own small wrapper classes.
"""


class QuillFunction:
    __slots__ = ("name", "params", "body", "closure")

    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self):
        return f"<fn {self.name or 'anonymous'}>"


class BuiltinFunction:
    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"<builtin {self.name}>"


def is_truthy(value) -> bool:
    if value is None or value is False:
        return False
    if value == 0 and isinstance(value, (int, float)) and not isinstance(value, bool):
        return False
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return False
    return True


def quill_equals(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(quill_equals(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(quill_equals(a[k], b[k]) for k in a)
    return a == b


def quill_str(value) -> str:
    """String conversion for print()/str() - human readable."""
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(quill_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{quill_repr(k)}: {quill_repr(v)}" for k, v in value.items()) + "}"
    return str(value)


def quill_repr(value) -> str:
    """Like quill_str, but strings get quoted - used for values nested inside lists/maps."""
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return quill_str(value)


def type_name(value) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "map"
    if isinstance(value, (QuillFunction, BuiltinFunction)):
        return "function"
    return "unknown"
