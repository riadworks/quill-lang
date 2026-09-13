"""Dot-method dispatch tables for built-in types: strings, lists, maps.

Each entry is fn(receiver, args, line) -> value, matching the same shape as a
builtin function so BoundBuiltinMethod can call it uniformly.
"""

from quill.errors import RuntimeErr
from quill.values import quill_equals, quill_str, type_name


def _arity(name, args, line, lo, hi=None):
    hi = lo if hi is None else hi
    if not (lo <= len(args) <= hi):
        want = str(lo) if lo == hi else f"{lo}-{hi}"
        raise RuntimeErr(f"{name}() expects {want} argument(s), got {len(args)}", line)


# ---------- string methods ----------

def _s_upper(s, args, line):
    _arity("upper", args, line, 0)
    return s.upper()


def _s_lower(s, args, line):
    _arity("lower", args, line, 0)
    return s.lower()


def _s_trim(s, args, line):
    _arity("trim", args, line, 0)
    return s.strip()


def _s_split(s, args, line):
    _arity("split", args, line, 0, 1)
    sep = args[0] if args else None
    return s.split(sep) if sep is not None else s.split()


def _s_replace(s, args, line):
    _arity("replace", args, line, 2)
    return s.replace(args[0], args[1])


def _s_contains(s, args, line):
    _arity("contains", args, line, 1)
    return args[0] in s


def _s_starts_with(s, args, line):
    _arity("starts_with", args, line, 1)
    return s.startswith(args[0])


def _s_ends_with(s, args, line):
    _arity("ends_with", args, line, 1)
    return s.endswith(args[0])


def _s_find(s, args, line):
    _arity("find", args, line, 1)
    return s.find(args[0])


def _s_repeat(s, args, line):
    _arity("repeat", args, line, 1)
    return s * int(args[0])


def _s_to_upper_words(s, args, line):
    _arity("title", args, line, 0)
    return s.title()


STRING_METHODS = {
    "upper": _s_upper,
    "lower": _s_lower,
    "trim": _s_trim,
    "split": _s_split,
    "replace": _s_replace,
    "contains": _s_contains,
    "starts_with": _s_starts_with,
    "ends_with": _s_ends_with,
    "find": _s_find,
    "repeat": _s_repeat,
    "title": _s_to_upper_words,
}


# ---------- list methods ----------

def _l_push(lst, args, line):
    _arity("push", args, line, 1)
    lst.append(args[0])
    return None


def _l_pop(lst, args, line):
    _arity("pop", args, line, 0)
    if not lst:
        raise RuntimeErr("pop() on an empty list", line)
    return lst.pop()


def _l_reverse(lst, args, line):
    _arity("reverse", args, line, 0)
    return list(reversed(lst))


def _l_sort(lst, args, line):
    _arity("sort", args, line, 0)
    return sorted(lst)


def _l_contains(lst, args, line):
    _arity("contains", args, line, 1)
    return any(quill_equals(x, args[0]) for x in lst)


def _l_index_of(lst, args, line):
    _arity("index_of", args, line, 1)
    for i, x in enumerate(lst):
        if quill_equals(x, args[0]):
            return i
    return -1


def _l_join(lst, args, line):
    _arity("join", args, line, 0, 1)
    sep = args[0] if args else ""
    return sep.join(quill_str(x) for x in lst)


def _l_map(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("map", args, line, 1)
    fn = args[0]
    return [CURRENT_INTERPRETER[0].call(fn, [x], line) for x in lst]


def _l_filter(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("filter", args, line, 1)
    fn = args[0]
    return [x for x in lst if is_truthy(CURRENT_INTERPRETER[0].call(fn, [x], line))]


def _l_reduce(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("reduce", args, line, 2)
    fn, init = args
    acc = init
    for x in lst:
        acc = CURRENT_INTERPRETER[0].call(fn, [acc, x], line)
    return acc


LIST_METHODS = {
    "push": _l_push,
    "pop": _l_pop,
    "reverse": _l_reverse,
    "sort": _l_sort,
    "contains": _l_contains,
    "index_of": _l_index_of,
    "join": _l_join,
    "map": _l_map,
    "filter": _l_filter,
    "reduce": _l_reduce,
}


# ---------- map methods ----------

def _m_keys(m, args, line):
    _arity("keys", args, line, 0)
    return list(m.keys())


def _m_values(m, args, line):
    _arity("values", args, line, 0)
    return list(m.values())


def _m_items(m, args, line):
    _arity("items", args, line, 0)
    return [[k, v] for k, v in m.items()]


def _m_has(m, args, line):
    _arity("has", args, line, 1)
    return args[0] in m


def _m_get(m, args, line):
    _arity("get", args, line, 1, 2)
    default = args[1] if len(args) == 2 else None
    return m.get(args[0], default)


MAP_METHODS = {
    "keys": _m_keys,
    "values": _m_values,
    "items": _m_items,
    "has": _m_has,
    "get": _m_get,
}
