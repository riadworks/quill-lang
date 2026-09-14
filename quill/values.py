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


class MroError(Exception):
    """Raised when a class's bases have no consistent method resolution order."""


def _c3_merge(sequences):
    sequences = [list(seq) for seq in sequences if seq]
    result = []
    while sequences:
        candidate = None
        for seq in sequences:
            head = seq[0]
            if not any(head in other[1:] for other in sequences):
                candidate = head
                break
        if candidate is None:
            raise MroError("cannot create a consistent method resolution order")
        result.append(candidate)
        for seq in sequences:
            if seq and seq[0] is candidate:
                del seq[0]
        sequences = [seq for seq in sequences if seq]
    return result


def compute_mro(superclasses):
    """C3-linearize a class's base list the way Python does: every ancestor
    appears exactly once, a class always precedes its own ancestors, and the
    declared left-to-right base order is preserved wherever the hierarchy
    allows it. This is what lets cooperative `super` calls walk a diamond
    (e.g. D(B, C) where both B and C extend A) and visit the shared ancestor
    exactly once, instead of the result depending on which branch happens to
    be searched first.
    """
    if not superclasses:
        return []
    return _c3_merge([list(s.mro) for s in superclasses] + [list(superclasses)])


class QuillClass:
    __slots__ = ("name", "methods", "superclasses", "mro")

    def __init__(self, name, methods, superclasses, mro):
        self.name = name
        self.methods = methods  # dict[str, QuillFunction]
        self.superclasses = superclasses  # list[QuillClass], declared order
        self.mro = mro  # list[QuillClass], self first, C3-linearized

    def find_method(self, name):
        for klass in self.mro:
            if name in klass.methods:
                return klass.methods[name]
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
    """`super` inside a method: resolves against the *instance's own* MRO,
    starting right after the class the currently-running method was defined
    in - not just that class's first declared base. That's what makes
    cooperative multiple inheritance work: a diamond's shared ancestor is
    reached once, in a consistent order, matching Python's `super()`.
    """

    __slots__ = ("instance", "owner_class")

    def __init__(self, instance, owner_class):
        self.instance = instance
        self.owner_class = owner_class

    def find_method(self, name):
        mro = self.instance.klass.mro
        try:
            start = mro.index(self.owner_class) + 1
        except ValueError:
            start = len(mro)
        for klass in mro[start:]:
            if name in klass.methods:
                return klass.methods[name]
        return None


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
