from quill.environment import Environment
from quill.errors import RuntimeErr
from quill.values import BuiltinFunction, quill_str, type_name


def _arity(name, args, line, lo, hi=None):
    hi = lo if hi is None else hi
    if not (lo <= len(args) <= hi):
        want = str(lo) if lo == hi else f"{lo}-{hi}"
        raise RuntimeErr(f"{name}() expects {want} argument(s), got {len(args)}", line)


def _require_number(name, value, line):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RuntimeErr(f"{name}() expects a number, got {type_name(value)}", line)
    return value


def _require_list(name, value, line):
    if not isinstance(value, list):
        raise RuntimeErr(f"{name}() expects a list, got {type_name(value)}", line)
    return value


def build_globals() -> Environment:
    env = Environment()

    def reg(name, fn):
        env.declare(name, BuiltinFunction(name, fn))

    def b_print(args, line):
        print(" ".join(quill_str(a) for a in args))
        return None

    def b_len(args, line):
        _arity("len", args, line, 1)
        v = args[0]
        if isinstance(v, (str, list, dict)):
            return len(v)
        raise RuntimeErr(f"len() doesn't work on {type_name(v)}", line)

    def b_type(args, line):
        _arity("type", args, line, 1)
        return type_name(args[0])

    def b_str(args, line):
        _arity("str", args, line, 1)
        return quill_str(args[0])

    def b_num(args, line):
        _arity("num", args, line, 1)
        v = args[0]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        if isinstance(v, str):
            try:
                return int(v) if v.strip().lstrip("-").isdigit() else float(v)
            except ValueError:
                raise RuntimeErr(f"cannot convert {v!r} to a number", line)
        raise RuntimeErr(f"cannot convert {type_name(v)} to a number", line)

    def b_bool(args, line):
        from quill.values import is_truthy

        _arity("bool", args, line, 1)
        return is_truthy(args[0])

    def b_range(args, line):
        _arity("range", args, line, 1, 3)
        nums = [int(_require_number("range", a, line)) for a in args]
        if len(nums) == 1:
            return list(range(nums[0]))
        if len(nums) == 2:
            return list(range(nums[0], nums[1]))
        return list(range(nums[0], nums[1], nums[2]))

    def b_input(args, line):
        _arity("input", args, line, 0, 1)
        prompt = quill_str(args[0]) if args else ""
        try:
            result = input(prompt)
        except EOFError:
            return ""
        # some Windows terminals/pipes (e.g. PowerShell piping a here-string into
        # stdin) prepend a UTF-8 BOM to the very first line - strip it so the
        # first input() call in a session doesn't silently fail an == comparison.
        return result.lstrip("﻿")

    def b_push(args, line):
        _arity("push", args, line, 2)
        lst = _require_list("push", args[0], line)
        lst.append(args[1])
        return None

    def b_pop(args, line):
        from quill.methods import _l_pop

        _arity("pop", args, line, 1, 2)
        lst = _require_list("pop", args[0], line)
        return _l_pop(lst, args[1:], line)

    def b_keys(args, line):
        _arity("keys", args, line, 1)
        if not isinstance(args[0], dict):
            raise RuntimeErr(f"keys() expects a map, got {type_name(args[0])}", line)
        return list(args[0].keys())

    def b_values(args, line):
        _arity("values", args, line, 1)
        if not isinstance(args[0], dict):
            raise RuntimeErr(f"values() expects a map, got {type_name(args[0])}", line)
        return list(args[0].values())

    def b_items(args, line):
        _arity("items", args, line, 1)
        if not isinstance(args[0], dict):
            raise RuntimeErr(f"items() expects a map, got {type_name(args[0])}", line)
        return [[k, v] for k, v in args[0].items()]

    def b_has(args, line):
        _arity("has", args, line, 2)
        container, needle = args
        if isinstance(container, dict):
            return needle in container
        if isinstance(container, list):
            from quill.values import quill_equals

            return any(quill_equals(x, needle) for x in container)
        if isinstance(container, str):
            return isinstance(needle, str) and needle in container
        raise RuntimeErr(f"has() doesn't work on {type_name(container)}", line)

    def b_sorted(args, line):
        _arity("sorted", args, line, 1)
        lst = _require_list("sorted", args[0], line)
        try:
            return sorted(lst)
        except TypeError:
            raise RuntimeErr("sorted() needs a list of all-comparable items (e.g. all numbers or all strings)", line)

    def b_sum(args, line):
        _arity("sum", args, line, 1)
        lst = _require_list("sum", args[0], line)
        total = 0
        for v in lst:
            total += _require_number("sum", v, line)
        return total

    def b_min(args, line):
        _arity("min", args, line, 1)
        lst = _require_list("min", args[0], line)
        if not lst:
            raise RuntimeErr("min() on an empty list", line)
        return min(lst)

    def b_max(args, line):
        _arity("max", args, line, 1)
        lst = _require_list("max", args[0], line)
        if not lst:
            raise RuntimeErr("max() on an empty list", line)
        return max(lst)

    def b_abs(args, line):
        _arity("abs", args, line, 1)
        return abs(_require_number("abs", args[0], line))

    def b_round(args, line):
        _arity("round", args, line, 1, 2)
        n = _require_number("round", args[0], line)
        digits = int(_require_number("round", args[1], line)) if len(args) == 2 else 0
        result = round(n, digits) if digits else round(n)
        return float(result) if digits else int(result)

    def b_slice(args, line):
        _arity("slice", args, line, 3)
        seq, start, end = args
        if not isinstance(seq, (list, str)):
            raise RuntimeErr(f"slice() expects a list or string, got {type_name(seq)}", line)
        start = int(_require_number("slice", start, line))
        end = int(_require_number("slice", end, line))
        return seq[start:end]

    def b_sqrt(args, line):
        import math

        _arity("sqrt", args, line, 1)
        n = _require_number("sqrt", args[0], line)
        if n < 0:
            raise RuntimeErr("sqrt() of a negative number", line)
        return math.sqrt(n)

    def b_floor(args, line):
        import math

        _arity("floor", args, line, 1)
        return math.floor(_require_number("floor", args[0], line))

    def b_ceil(args, line):
        import math

        _arity("ceil", args, line, 1)
        return math.ceil(_require_number("ceil", args[0], line))

    def b_enumerate(args, line):
        _arity("enumerate", args, line, 1)
        lst = _require_list("enumerate", args[0], line)
        return [[i, v] for i, v in enumerate(lst)]

    def b_zip(args, line):
        _arity("zip", args, line, 2)
        a = _require_list("zip", args[0], line)
        b = _require_list("zip", args[1], line)
        return [[x, y] for x, y in zip(a, b)]

    def b_read_file(args, line):
        _arity("read_file", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"read_file() expects a string path, got {type_name(path)}", line)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as exc:
            raise RuntimeErr(f"cannot read '{path}': {exc.strerror}", line)

    def b_write_file(args, line):
        _arity("write_file", args, line, 2)
        path, content = args
        if not isinstance(path, str):
            raise RuntimeErr(f"write_file() expects a string path, got {type_name(path)}", line)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(quill_str(content))
        except OSError as exc:
            raise RuntimeErr(f"cannot write '{path}': {exc.strerror}", line)
        return None

    def b_file_exists(args, line):
        import os

        _arity("file_exists", args, line, 1)
        return os.path.isfile(args[0])

    def b_serve(args, line):
        from quill.interpreter import CURRENT_INTERPRETER
        from quill.webserver import serve as run_server

        _arity("serve", args, line, 2)
        port, handler = args
        port = int(_require_number("serve", port, line))
        interp = CURRENT_INTERPRETER[0]
        run_server(port, handler, interp.call)
        return None

    def b_url_encode(args, line):
        import urllib.parse

        _arity("url_encode", args, line, 1)
        return urllib.parse.quote(quill_str(args[0]))

    reg("print", b_print)
    reg("len", b_len)
    reg("type", b_type)
    reg("str", b_str)
    reg("num", b_num)
    reg("bool", b_bool)
    reg("range", b_range)
    reg("input", b_input)
    reg("push", b_push)
    reg("pop", b_pop)
    reg("keys", b_keys)
    reg("values", b_values)
    reg("items", b_items)
    reg("has", b_has)
    reg("sorted", b_sorted)
    reg("sum", b_sum)
    reg("min", b_min)
    reg("max", b_max)
    reg("abs", b_abs)
    reg("round", b_round)
    reg("slice", b_slice)
    reg("sqrt", b_sqrt)
    reg("floor", b_floor)
    reg("ceil", b_ceil)
    reg("enumerate", b_enumerate)
    reg("zip", b_zip)
    reg("read_file", b_read_file)
    reg("write_file", b_write_file)
    reg("file_exists", b_file_exists)
    reg("serve", b_serve)
    reg("url_encode", b_url_encode)
    env.declare("PI", 3.141592653589793)

    return env
