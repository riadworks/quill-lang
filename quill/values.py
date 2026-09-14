"""Runtime value representations and formatting helpers.

Quill values map onto native Python types where possible: numbers -> int/float,
strings -> str, booleans -> bool, nil -> None, lists -> list, maps -> dict.
User-defined functions and built-ins get their own small wrapper classes.
"""

from quill.errors import RuntimeErr


class QuillFunction:
    __slots__ = ("name", "params", "defaults", "body", "closure", "owner_class")

    def __init__(self, name, params, defaults, body, closure, owner_class=None):
        self.name = name
        self.params = params
        self.defaults = defaults
        self.body = body
        self.closure = closure
        # the class this was defined in as a method, if any - lets `super` inside it
        # resolve to *that class's* parent, regardless of the runtime instance's own
        # (possibly further-subclassed) type. Without this, super chains beyond one
        # level would resolve against the wrong class and loop instead of climbing.
        self.owner_class = owner_class

    def __repr__(self):
        return f"<pull {self.name or 'anonymous'}>"


class BuiltinFunction:
    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"<builtin {self.name}>"


class QuillClass:
    __slots__ = ("name", "methods", "superclass")

    def __init__(self, name, methods, superclass=None):
        self.name = name
        self.methods = methods  # dict[str, QuillFunction]
        self.superclass = superclass

    def find_method(self, name):
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None

    def __repr__(self):
        return f"<class {self.name}>"


class QuillInstance:
    __slots__ = ("klass", "fields")

    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def __repr__(self):
        return f"<{self.klass.name} instance>"


class BoundInstanceMethod:
    __slots__ = ("instance", "func")

    def __init__(self, instance, func):
        self.instance = instance
        self.func = func

    def __repr__(self):
        return f"<bound method {self.func.name}>"


class SuperProxy:
    __slots__ = ("instance", "superclass")

    def __init__(self, instance, superclass):
        self.instance = instance
        self.superclass = superclass


class BoundBuiltinMethod:
    __slots__ = ("receiver", "name", "fn")

    def __init__(self, receiver, name, fn):
        self.receiver = receiver
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"<bound builtin method {self.name}>"


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
    if isinstance(value, QuillInstance):
        method = value.klass.find_method("__str__")
        if method is not None:
            from quill.interpreter import CURRENT_INTERPRETER

            result = CURRENT_INTERPRETER[0].call(BoundInstanceMethod(value, method), [], 0)
            if not isinstance(result, str):
                raise RuntimeErr(f"__str__() must return a string, got {type_name(result)}", 0)
            return result
    return repr(value)


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
    if isinstance(value, (QuillFunction, BuiltinFunction, BoundInstanceMethod, BoundBuiltinMethod)):
        return "function"
    if isinstance(value, QuillClass):
        return "class"
    if isinstance(value, QuillInstance):
        return value.klass.name
    return "unknown"
