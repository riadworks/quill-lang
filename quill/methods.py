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


def _require_num(name, value, line):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RuntimeErr(f"{name}() expects a number, got {type_name(value)}", line)
    return value


def _is_callable(v):
    from quill.values import BoundBuiltinMethod, BoundInstanceMethod, BuiltinFunction, QuillFunction

    return isinstance(v, (QuillFunction, BuiltinFunction, BoundInstanceMethod, BoundBuiltinMethod))


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


def _s_trim_start(s, args, line):
    _arity("trim_start", args, line, 0)
    return s.lstrip()


def _s_trim_end(s, args, line):
    _arity("trim_end", args, line, 0)
    return s.rstrip()


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


def _s_index(s, args, line):
    _arity("index", args, line, 1)
    i = s.find(args[0])
    if i == -1:
        raise RuntimeErr(f"substring not found: {args[0]!r}", line)
    return i


def _s_count(s, args, line):
    _arity("count", args, line, 1)
    return s.count(args[0])


def _s_repeat(s, args, line):
    _arity("repeat", args, line, 1)
    return s * int(_require_num("repeat", args[0], line))


def _s_pad_start(s, args, line):
    _arity("pad_start", args, line, 1, 2)
    width = int(_require_num("pad_start", args[0], line))
    fill = args[1] if len(args) == 2 else " "
    if not isinstance(fill, str) or len(fill) != 1:
        raise RuntimeErr("pad_start() fill must be a single character", line)
    return s.rjust(width, fill)


def _s_pad_end(s, args, line):
    _arity("pad_end", args, line, 1, 2)
    width = int(_require_num("pad_end", args[0], line))
    fill = args[1] if len(args) == 2 else " "
    if not isinstance(fill, str) or len(fill) != 1:
        raise RuntimeErr("pad_end() fill must be a single character", line)
    return s.ljust(width, fill)


def _s_to_upper_words(s, args, line):
    _arity("title", args, line, 0)
    return s.title()


def _s_capitalize(s, args, line):
    _arity("capitalize", args, line, 0)
    return s.capitalize()


def _s_swap_case(s, args, line):
    _arity("swap_case", args, line, 0)
    return s.swapcase()


def _s_reverse(s, args, line):
    _arity("reverse", args, line, 0)
    return s[::-1]


def _s_is_digit(s, args, line):
    _arity("is_digit", args, line, 0)
    return s.isdigit()


def _s_is_alpha(s, args, line):
    _arity("is_alpha", args, line, 0)
    return s.isalpha()


def _s_is_alnum(s, args, line):
    _arity("is_alnum", args, line, 0)
    return s.isalnum()


def _s_is_upper(s, args, line):
    _arity("is_upper", args, line, 0)
    return s.isupper()


def _s_is_lower(s, args, line):
    _arity("is_lower", args, line, 0)
    return s.islower()


def _s_is_space(s, args, line):
    _arity("is_space", args, line, 0)
    return s.isspace()


def _s_center(s, args, line):
    _arity("center", args, line, 1, 2)
    width = int(_require_num("center", args[0], line))
    fill = args[1] if len(args) == 2 else " "
    if not isinstance(fill, str) or len(fill) != 1:
        raise RuntimeErr("center() fill must be a single character", line)
    return s.center(width, fill)


def _s_zfill(s, args, line):
    _arity("zfill", args, line, 1)
    width = int(_require_num("zfill", args[0], line))
    return s.zfill(width)


def _s_remove_prefix(s, args, line):
    _arity("remove_prefix", args, line, 1)
    prefix = args[0]
    return s[len(prefix):] if prefix and s.startswith(prefix) else s


def _s_remove_suffix(s, args, line):
    _arity("remove_suffix", args, line, 1)
    suffix = args[0]
    return s[: -len(suffix)] if suffix and s.endswith(suffix) else s


def _s_split_lines(s, args, line):
    _arity("split_lines", args, line, 0)
    return s.splitlines()


STRING_METHODS = {
    "upper": _s_upper,
    "lower": _s_lower,
    "trim": _s_trim,
    "trim_start": _s_trim_start,
    "trim_end": _s_trim_end,
    "split": _s_split,
    "replace": _s_replace,
    "contains": _s_contains,
    "starts_with": _s_starts_with,
    "ends_with": _s_ends_with,
    "find": _s_find,
    "index": _s_index,
    "count": _s_count,
    "repeat": _s_repeat,
    "pad_start": _s_pad_start,
    "pad_end": _s_pad_end,
    "title": _s_to_upper_words,
    "capitalize": _s_capitalize,
    "swap_case": _s_swap_case,
    "reverse": _s_reverse,
    "is_digit": _s_is_digit,
    "is_alpha": _s_is_alpha,
    "is_alnum": _s_is_alnum,
    "is_upper": _s_is_upper,
    "is_lower": _s_is_lower,
    "is_space": _s_is_space,
    "center": _s_center,
    "zfill": _s_zfill,
    "remove_prefix": _s_remove_prefix,
    "remove_suffix": _s_remove_suffix,
    "split_lines": _s_split_lines,
}


# ---------- list methods ----------

def _l_push(lst, args, line):
    _arity("push", args, line, 1)
    lst.append(args[0])
    return None


def _l_pop(lst, args, line):
    _arity("pop", args, line, 0, 1)
    if not lst:
        raise RuntimeErr("pop() on an empty list", line)
    if not args:
        return lst.pop()
    index = args[0]
    if not isinstance(index, int) or isinstance(index, bool):
        raise RuntimeErr(f"pop() index must be a number, got {type_name(index)}", line)
    if index < 0:
        index += len(lst)
    if not (0 <= index < len(lst)):
        raise RuntimeErr("pop() index out of range", line)
    return lst.pop(index)


def _l_insert(lst, args, line):
    _arity("insert", args, line, 2)
    index = args[0]
    if not isinstance(index, int) or isinstance(index, bool):
        raise RuntimeErr(f"insert() index must be a number, got {type_name(index)}", line)
    lst.insert(index, args[1])
    return None


def _l_remove(lst, args, line):
    _arity("remove", args, line, 1)
    for i, x in enumerate(lst):
        if quill_equals(x, args[0]):
            lst.pop(i)
            return None
    raise RuntimeErr("remove(): value not found in list", line)


def _l_clear(lst, args, line):
    _arity("clear", args, line, 0)
    lst.clear()
    return None


def _l_copy(lst, args, line):
    _arity("copy", args, line, 0)
    return list(lst)


def _l_extend(lst, args, line):
    _arity("extend", args, line, 1)
    other = args[0]
    if not isinstance(other, list):
        raise RuntimeErr(f"extend() expects a list, got {type_name(other)}", line)
    lst.extend(other)
    return None


def _l_count(lst, args, line):
    _arity("count", args, line, 1)
    return sum(1 for x in lst if quill_equals(x, args[0]))


def _l_unique(lst, args, line):
    _arity("unique", args, line, 0)
    result = []
    for x in lst:
        if not any(quill_equals(x, seen) for seen in result):
            result.append(x)
    return result


def _l_flatten(lst, args, line):
    _arity("flatten", args, line, 0)
    result = []
    for x in lst:
        if isinstance(x, list):
            result.extend(x)
        else:
            result.append(x)
    return result


def _l_reverse(lst, args, line):
    _arity("reverse", args, line, 0)
    return list(reversed(lst))


def sort_with_options(lst, extra_args, line, label="sort"):
    """Shared by the .sort() method and the sorted() builtin. extra_args is
    0-2 positional values: a key function and/or a reverse bool, in either
    order - whichever is callable is the key, whichever is a bool is
    reverse, so there's no ambiguity without needing keyword arguments."""
    from quill.interpreter import CURRENT_INTERPRETER

    key_fn = None
    reverse = False
    for a in extra_args:
        if isinstance(a, bool):
            reverse = a
        elif _is_callable(a):
            key_fn = a
        else:
            raise RuntimeErr(f"{label}() extra arguments must be a key function and/or a bool", line)

    if key_fn is not None:
        interp = CURRENT_INTERPRETER[0]
        try:
            return sorted(lst, key=lambda x: interp.call(key_fn, [x], line), reverse=reverse)
        except TypeError:
            raise RuntimeErr(f"{label}() key function must return all-comparable values", line)
    try:
        return sorted(lst, reverse=reverse)
    except TypeError:
        raise RuntimeErr(
            f"{label}() needs a list of all-comparable items (e.g. all numbers or all strings)", line
        )


def _l_sort(lst, args, line):
    _arity("sort", args, line, 0, 2)
    return sort_with_options(lst, args, line, label="sort")


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


def _l_chunk(lst, args, line):
    _arity("chunk", args, line, 1)
    n = args[0]
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise RuntimeErr("chunk() size must be a positive whole number", line)
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def _l_group_by(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("group_by", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    result = {}
    for x in lst:
        key = interp.call(fn, [x], line)
        if not isinstance(key, (str, int, float, bool)):
            raise RuntimeErr(
                f"group_by() key function must return a string, number, or bool, not {type_name(key)}", line
            )
        result.setdefault(key, []).append(x)
    return result


def _l_flat_map(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("flat_map", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    result = []
    for x in lst:
        mapped = interp.call(fn, [x], line)
        if isinstance(mapped, list):
            result.extend(mapped)
        else:
            result.append(mapped)
    return result


LIST_METHODS = {
    "push": _l_push,
    "pop": _l_pop,
    "insert": _l_insert,
    "remove": _l_remove,
    "clear": _l_clear,
    "copy": _l_copy,
    "extend": _l_extend,
    "count": _l_count,
    "unique": _l_unique,
    "flatten": _l_flatten,
    "reverse": _l_reverse,
    "sort": _l_sort,
    "contains": _l_contains,
    "index_of": _l_index_of,
    "join": _l_join,
    "map": _l_map,
    "filter": _l_filter,
    "reduce": _l_reduce,
    "chunk": _l_chunk,
    "group_by": _l_group_by,
    "flat_map": _l_flat_map,
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


def _m_pop(m, args, line):
    _arity("pop", args, line, 1, 2)
    if len(args) == 2:
        return m.pop(args[0], args[1])
    if args[0] not in m:
        raise RuntimeErr(f"pop(): key not found: {args[0]!r}", line)
    return m.pop(args[0])


def _m_clear(m, args, line):
    _arity("clear", args, line, 0)
    m.clear()
    return None


def _m_copy(m, args, line):
    _arity("copy", args, line, 0)
    return dict(m)


def _m_update(m, args, line):
    _arity("update", args, line, 1)
    other = args[0]
    if not isinstance(other, dict):
        raise RuntimeErr(f"update() expects a map, got {type_name(other)}", line)
    m.update(other)
    return None


def _m_setdefault(m, args, line):
    _arity("setdefault", args, line, 2)
    return m.setdefault(args[0], args[1])


MAP_METHODS = {
    "keys": _m_keys,
    "values": _m_values,
    "items": _m_items,
    "has": _m_has,
    "get": _m_get,
    "pop": _m_pop,
    "clear": _m_clear,
    "copy": _m_copy,
    "update": _m_update,
    "setdefault": _m_setdefault,
}
