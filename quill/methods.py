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


def _require_number(name, value, line):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RuntimeErr(f"{name}() expects a number, got {type_name(value)}", line)
    return value


def _require_str(name, value, line):
    if not isinstance(value, str):
        raise RuntimeErr(f"{name}() expects a string argument, got {type_name(value)}", line)
    return value


def _require_map_key(name, value, line):
    if not isinstance(value, (str, int, float, bool)):
        raise RuntimeErr(f"{name}() map keys must be a string, number, or bool, not {type_name(value)}", line)
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
    sep = _require_str("split", args[0], line) if args else None
    return s.split(sep) if sep is not None else s.split()


def _s_replace(s, args, line):
    _arity("replace", args, line, 2)
    return s.replace(_require_str("replace", args[0], line), _require_str("replace", args[1], line))


def _s_contains(s, args, line):
    _arity("contains", args, line, 1)
    return _require_str("contains", args[0], line) in s


def _s_starts_with(s, args, line):
    _arity("starts_with", args, line, 1)
    return s.startswith(_require_str("starts_with", args[0], line))


def _s_ends_with(s, args, line):
    _arity("ends_with", args, line, 1)
    return s.endswith(_require_str("ends_with", args[0], line))


def _s_find(s, args, line):
    _arity("find", args, line, 1)
    return s.find(_require_str("find", args[0], line))


def _s_index(s, args, line):
    _arity("index", args, line, 1)
    needle = _require_str("index", args[0], line)
    i = s.find(needle)
    if i == -1:
        raise RuntimeErr(f"substring not found: {needle!r}", line)
    return i


def _s_count(s, args, line):
    _arity("count", args, line, 1)
    return s.count(_require_str("count", args[0], line))


def _s_repeat(s, args, line):
    _arity("repeat", args, line, 1)
    return s * int(_require_number("repeat", args[0], line))


def _s_pad_start(s, args, line):
    _arity("pad_start", args, line, 1, 2)
    width = int(_require_number("pad_start", args[0], line))
    fill = args[1] if len(args) == 2 else " "
    if not isinstance(fill, str) or len(fill) != 1:
        raise RuntimeErr("pad_start() fill must be a single character", line)
    return s.rjust(width, fill)


def _s_pad_end(s, args, line):
    _arity("pad_end", args, line, 1, 2)
    width = int(_require_number("pad_end", args[0], line))
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


def _s_is_ascii(s, args, line):
    _arity("is_ascii", args, line, 0)
    return s.isascii()


def _s_byte_length(s, args, line):
    _arity("byte_length", args, line, 0)
    return len(s.encode("utf-8"))


def _to_words(s):
    """Splits a string on case boundaries and separators, for the case-
    conversion methods below - the standard two-pass approach that correctly
    handles a leading acronym ('XMLHttpRequest' -> ['XML', 'Http', 'Request']),
    not just a simple camelCase boundary."""
    import re

    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return [p for p in re.split(r"[\s_\-]+", s2) if p]


def _s_to_snake_case(s, args, line):
    _arity("to_snake_case", args, line, 0)
    return "_".join(w.lower() for w in _to_words(s))


def _s_to_kebab_case(s, args, line):
    _arity("to_kebab_case", args, line, 0)
    return "-".join(w.lower() for w in _to_words(s))


def _s_to_camel_case(s, args, line):
    _arity("to_camel_case", args, line, 0)
    words = _to_words(s)
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


def _s_center(s, args, line):
    _arity("center", args, line, 1, 2)
    width = int(_require_number("center", args[0], line))
    fill = args[1] if len(args) == 2 else " "
    if not isinstance(fill, str) or len(fill) != 1:
        raise RuntimeErr("center() fill must be a single character", line)
    return s.center(width, fill)


def _s_zfill(s, args, line):
    _arity("zfill", args, line, 1)
    width = int(_require_number("zfill", args[0], line))
    return s.zfill(width)


def _s_remove_prefix(s, args, line):
    _arity("remove_prefix", args, line, 1)
    prefix = _require_str("remove_prefix", args[0], line)
    return s[len(prefix):] if prefix and s.startswith(prefix) else s


def _s_remove_suffix(s, args, line):
    _arity("remove_suffix", args, line, 1)
    suffix = _require_str("remove_suffix", args[0], line)
    return s[: -len(suffix)] if suffix and s.endswith(suffix) else s


def _s_split_lines(s, args, line):
    _arity("split_lines", args, line, 0)
    return s.splitlines()


def _s_equals_ignore_case(s, args, line):
    _arity("equals_ignore_case", args, line, 1)
    return s.lower() == _require_str("equals_ignore_case", args[0], line).lower()


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
    "is_ascii": _s_is_ascii,
    "byte_length": _s_byte_length,
    "to_snake_case": _s_to_snake_case,
    "to_kebab_case": _s_to_kebab_case,
    "to_camel_case": _s_to_camel_case,
    "equals_ignore_case": _s_equals_ignore_case,
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
    raise RuntimeErr(f"value not found in list: {args[0]!r}", line)


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


def _l_union(lst, args, line):
    _arity("union", args, line, 1)
    other = args[0]
    if not isinstance(other, list):
        raise RuntimeErr(f"union() expects a list, got {type_name(other)}", line)
    result = []
    for x in list(lst) + list(other):
        if not any(quill_equals(x, y) for y in result):
            result.append(x)
    return result


def _l_intersect(lst, args, line):
    _arity("intersect", args, line, 1)
    other = args[0]
    if not isinstance(other, list):
        raise RuntimeErr(f"intersect() expects a list, got {type_name(other)}", line)
    result = []
    for x in lst:
        if any(quill_equals(x, y) for y in other) and not any(quill_equals(x, y) for y in result):
            result.append(x)
    return result


def _l_difference(lst, args, line):
    _arity("difference", args, line, 1)
    other = args[0]
    if not isinstance(other, list):
        raise RuntimeErr(f"difference() expects a list, got {type_name(other)}", line)
    result = []
    for x in lst:
        if not any(quill_equals(x, y) for y in other) and not any(quill_equals(x, y) for y in result):
            result.append(x)
    return result


def _require_nonneg_int(name, value, line):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RuntimeErr(f"{name}() count must be a non-negative whole number", line)
    return value


def _l_take(lst, args, line):
    _arity("take", args, line, 1)
    n = _require_nonneg_int("take", args[0], line)
    return lst[:n]


def _l_drop(lst, args, line):
    _arity("drop", args, line, 1)
    n = _require_nonneg_int("drop", args[0], line)
    return lst[n:]


def _l_take_last(lst, args, line):
    _arity("take_last", args, line, 1)
    n = _require_nonneg_int("take_last", args[0], line)
    return lst[len(lst) - n :] if n > 0 else []


def _l_drop_last(lst, args, line):
    _arity("drop_last", args, line, 1)
    n = _require_nonneg_int("drop_last", args[0], line)
    return lst[: len(lst) - n] if n > 0 else list(lst)


def _l_take_while(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("take_while", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    result = []
    for x in lst:
        if not is_truthy(interp.call(fn, [x], line)):
            break
        result.append(x)
    return result


def _l_drop_while(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("drop_while", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    i = 0
    while i < len(lst) and is_truthy(interp.call(fn, [lst[i]], line)):
        i += 1
    return lst[i:]


def _l_find(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("find", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    for x in lst:
        if is_truthy(interp.call(fn, [x], line)):
            return x
    return None


def _l_find_index(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("find_index", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    for i, x in enumerate(lst):
        if is_truthy(interp.call(fn, [x], line)):
            return i
    return -1


def _l_partition(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("partition", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    yes, no = [], []
    for x in lst:
        (yes if is_truthy(interp.call(fn, [x], line)) else no).append(x)
    return [yes, no]


def _l_tally(lst, args, line):
    _arity("tally", args, line, 0)
    result = {}
    for x in lst:
        if not isinstance(x, (str, int, float, bool)):
            raise RuntimeErr(f"tally() needs elements that are strings, numbers, or bools, not {type_name(x)}", line)
        result[x] = result.get(x, 0) + 1
    return result


def _l_every(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("every", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    return all(is_truthy(interp.call(fn, [x], line)) for x in lst)


def _l_some(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER
    from quill.values import is_truthy

    _arity("some", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    return any(is_truthy(interp.call(fn, [x], line)) for x in lst)


def _l_zip_with(lst, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("zip_with", args, line, 2)
    other, fn = args
    if not isinstance(other, list):
        raise RuntimeErr(f"zip_with() expects a list, got {type_name(other)}", line)
    interp = CURRENT_INTERPRETER[0]
    return [interp.call(fn, [a, b], line) for a, b in zip(lst, other)]


def _l_rotate(lst, args, line):
    _arity("rotate", args, line, 1)
    n = args[0]
    if not isinstance(n, int) or isinstance(n, bool):
        raise RuntimeErr("rotate() amount must be a whole number", line)
    if not lst:
        return []
    n = n % len(lst)
    return lst[n:] + lst[:n]


def _l_shuffle(lst, args, line):
    import random as _random

    _arity("shuffle", args, line, 0)
    result = list(lst)
    _random.shuffle(result)
    return result


def _l_choice(lst, args, line):
    import random as _random

    _arity("choice", args, line, 0)
    if not lst:
        raise RuntimeErr("choice() on an empty list", line)
    return _random.choice(lst)


def _l_first(lst, args, line):
    _arity("first", args, line, 0)
    if not lst:
        raise RuntimeErr("first() on an empty list", line)
    return lst[0]


def _l_last(lst, args, line):
    _arity("last", args, line, 0)
    if not lst:
        raise RuntimeErr("last() on an empty list", line)
    return lst[-1]


def _l_last_index_of(lst, args, line):
    _arity("last_index_of", args, line, 1)
    for i in range(len(lst) - 1, -1, -1):
        if quill_equals(lst[i], args[0]):
            return i
    return -1


def _l_repeat(lst, args, line):
    _arity("repeat", args, line, 1)
    n = _require_nonneg_int("repeat", args[0], line)
    return lst * n


def _l_flatten_deep(lst, args, line):
    _arity("flatten_deep", args, line, 0)
    result = []

    def _go(items):
        for x in items:
            if isinstance(x, list):
                _go(x)
            else:
                result.append(x)

    _go(lst)
    return result


def _l_pairwise(lst, args, line):
    _arity("pairwise", args, line, 0)
    return [[lst[i], lst[i + 1]] for i in range(len(lst) - 1)]


def _l_min(lst, args, line):
    _arity("min", args, line, 0, 1)
    if not lst:
        raise RuntimeErr("min() on an empty list", line)
    if args:
        from quill.interpreter import CURRENT_INTERPRETER

        interp = CURRENT_INTERPRETER[0]
        key_fn = args[0]
        try:
            return min(lst, key=lambda x: interp.call(key_fn, [x], line))
        except TypeError:
            raise RuntimeErr("min() key function must return all-comparable values", line)
    try:
        return min(lst)
    except TypeError:
        raise RuntimeErr("min() needs a list of all-comparable items", line)


def _l_max(lst, args, line):
    _arity("max", args, line, 0, 1)
    if not lst:
        raise RuntimeErr("max() on an empty list", line)
    if args:
        from quill.interpreter import CURRENT_INTERPRETER

        interp = CURRENT_INTERPRETER[0]
        key_fn = args[0]
        try:
            return max(lst, key=lambda x: interp.call(key_fn, [x], line))
        except TypeError:
            raise RuntimeErr("max() key function must return all-comparable values", line)
    try:
        return max(lst)
    except TypeError:
        raise RuntimeErr("max() needs a list of all-comparable items", line)


def _l_sum(lst, args, line):
    _arity("sum", args, line, 0)
    total = 0
    for x in lst:
        total += _require_number("sum", x, line)
    return total


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
    "union": _l_union,
    "intersect": _l_intersect,
    "difference": _l_difference,
    "take": _l_take,
    "drop": _l_drop,
    "take_last": _l_take_last,
    "drop_last": _l_drop_last,
    "take_while": _l_take_while,
    "drop_while": _l_drop_while,
    "find": _l_find,
    "find_index": _l_find_index,
    "partition": _l_partition,
    "tally": _l_tally,
    "every": _l_every,
    "some": _l_some,
    "zip_with": _l_zip_with,
    "rotate": _l_rotate,
    "shuffle": _l_shuffle,
    "choice": _l_choice,
    "first": _l_first,
    "last": _l_last,
    "last_index_of": _l_last_index_of,
    "repeat": _l_repeat,
    "flatten_deep": _l_flatten_deep,
    "pairwise": _l_pairwise,
    "min": _l_min,
    "max": _l_max,
    "sum": _l_sum,
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
    return _require_map_key("has", args[0], line) in m


def _m_get(m, args, line):
    _arity("get", args, line, 1, 2)
    default = args[1] if len(args) == 2 else None
    return m.get(_require_map_key("get", args[0], line), default)


def _m_pop(m, args, line):
    _arity("pop", args, line, 1, 2)
    key = _require_map_key("pop", args[0], line)
    if len(args) == 2:
        return m.pop(key, args[1])
    if key not in m:
        raise RuntimeErr(f"key not found: {key!r}", line)
    return m.pop(key)


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
    return m.setdefault(_require_map_key("setdefault", args[0], line), args[1])


def _m_map_values(m, args, line):
    from quill.interpreter import CURRENT_INTERPRETER

    _arity("map_values", args, line, 1)
    fn = args[0]
    interp = CURRENT_INTERPRETER[0]
    return {k: interp.call(fn, [v], line) for k, v in m.items()}


def _m_merged(m, args, line):
    _arity("merged", args, line, 1)
    other = args[0]
    if not isinstance(other, dict):
        raise RuntimeErr(f"merged() expects a map, got {type_name(other)}", line)
    result = dict(m)
    result.update(other)
    return result


def _m_invert(m, args, line):
    _arity("invert", args, line, 0)
    result = {}
    for k, v in m.items():
        if not isinstance(v, (str, int, float, bool)):
            raise RuntimeErr(f"invert() needs values that are strings, numbers, or bools, not {type_name(v)}", line)
        result[v] = k
    return result


def _m_pick(m, args, line):
    _arity("pick", args, line, 1)
    keys = args[0]
    if not isinstance(keys, list):
        raise RuntimeErr(f"pick() expects a list of keys, got {type_name(keys)}", line)
    return {k: m[k] for k in keys if k in m}


def _m_omit(m, args, line):
    _arity("omit", args, line, 1)
    keys = args[0]
    if not isinstance(keys, list):
        raise RuntimeErr(f"omit() expects a list of keys, got {type_name(keys)}", line)
    excluded = set(keys)
    return {k: v for k, v in m.items() if k not in excluded}


def _m_key_of(m, args, line):
    _arity("key_of", args, line, 1)
    target = args[0]
    for k, v in m.items():
        if quill_equals(v, target):
            return k
    return None


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
    "map_values": _m_map_values,
    "merged": _m_merged,
    "invert": _m_invert,
    "pick": _m_pick,
    "omit": _m_omit,
    "key_of": _m_key_of,
}
