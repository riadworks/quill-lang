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


def build_globals(script_args=None) -> Environment:
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
            if not isinstance(needle, (str, int, float, bool)):
                raise RuntimeErr(f"has() map keys must be a string, number, or bool, not {type_name(needle)}", line)
            return needle in container
        if isinstance(container, list):
            from quill.values import quill_equals

            return any(quill_equals(x, needle) for x in container)
        if isinstance(container, str):
            return isinstance(needle, str) and needle in container
        raise RuntimeErr(f"has() doesn't work on {type_name(container)}", line)

    def b_sorted(args, line):
        from quill.methods import sort_with_options

        _arity("sorted", args, line, 1, 3)
        lst = _require_list("sorted", args[0], line)
        return sort_with_options(lst, args[1:], line, label="sorted")

    def b_sum(args, line):
        _arity("sum", args, line, 1)
        lst = _require_list("sum", args[0], line)
        total = 0
        for v in lst:
            total += _require_number("sum", v, line)
        return total

    def _min_max(name, py_fn, args, line):
        _arity(name, args, line, 1, 2)
        lst = _require_list(name, args[0], line)
        if not lst:
            raise RuntimeErr(f"{name}() on an empty list", line)
        if len(args) == 2:
            from quill.interpreter import CURRENT_INTERPRETER

            key_fn = args[1]
            return py_fn(lst, key=lambda x: CURRENT_INTERPRETER[0].call(key_fn, [x], line))
        try:
            return py_fn(lst)
        except TypeError:
            raise RuntimeErr(f"{name}() needs a list of all-comparable items", line)

    def b_min(args, line):
        return _min_max("min", min, args, line)

    def b_max(args, line):
        return _min_max("max", max, args, line)

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

    def _headers_to_dict(headers, who, line):
        if headers is None:
            return {}
        if not isinstance(headers, dict):
            raise RuntimeErr(f"{who}() headers argument must be a map, got {type_name(headers)}", line)
        return {str(k): quill_str(v) for k, v in headers.items()}

    def _do_http_request(method, url, body_bytes, headers, line):
        import urllib.error
        import urllib.request

        if not isinstance(url, str):
            raise RuntimeErr(f"http_{method.lower()}() expects a string URL, got {type_name(url)}", line)
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return {"status": resp.status, "body": raw, "headers": dict(resp.headers)}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return {"status": exc.code, "body": raw, "headers": dict(exc.headers or {})}
        except urllib.error.URLError as exc:
            raise RuntimeErr(f"http_{method.lower()}() failed: {exc.reason}", line)

    def b_http_get(args, line):
        _arity("http_get", args, line, 1, 2)
        headers = _headers_to_dict(args[1] if len(args) == 2 else None, "http_get", line)
        return _do_http_request("GET", args[0], None, headers, line)

    def b_http_post(args, line):
        _arity("http_post", args, line, 2, 3)
        headers = _headers_to_dict(args[2] if len(args) == 3 else None, "http_post", line)
        body = args[1]
        if isinstance(body, dict):
            import urllib.parse

            body_bytes = urllib.parse.urlencode({str(k): quill_str(v) for k, v in body.items()}).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        elif isinstance(body, str):
            body_bytes = body.encode("utf-8")
        else:
            raise RuntimeErr(f"http_post() body must be a string or a map, got {type_name(body)}", line)
        return _do_http_request("POST", args[0], body_bytes, headers, line)

    def _to_json_safe(value, line):
        # Quill's own runtime types (dict/list/str/int/float/bool/None) already match
        # Python's json module's expectations exactly - the one thing that needs
        # rejecting explicitly is a function/class/instance, which json would otherwise
        # fail on with a confusing native TypeError instead of a clear Quill error.
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [_to_json_safe(v, line) for v in value]
        if isinstance(value, dict):
            return {str(k): _to_json_safe(v, line) for k, v in value.items()}
        raise RuntimeErr(f"json_encode() can't serialize a {type_name(value)}", line)

    def b_json_encode(args, line):
        import json

        _arity("json_encode", args, line, 1, 2)
        pretty = len(args) == 2 and args[1]
        safe = _to_json_safe(args[0], line)
        return json.dumps(safe, indent=2 if pretty else None)

    def b_json_decode(args, line):
        import json

        _arity("json_decode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"json_decode() expects a string, got {type_name(text)}", line)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeErr(f"invalid JSON: {exc.msg}", line)

    def b_sha256(args, line):
        import hashlib

        _arity("sha256", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"sha256() expects a string, got {type_name(text)}", line)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    _PBKDF2_ITERATIONS = 260_000

    def b_password_hash(args, line):
        import binascii
        import hashlib
        import os

        _arity("password_hash", args, line, 1)
        password = args[0]
        if not isinstance(password, str):
            raise RuntimeErr(f"password_hash() expects a string, got {type_name(password)}", line)
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return (
            f"pbkdf2_sha256${_PBKDF2_ITERATIONS}$"
            f"{binascii.hexlify(salt).decode()}${binascii.hexlify(digest).decode()}"
        )

    def b_password_verify(args, line):
        import binascii
        import hashlib
        import hmac

        _arity("password_verify", args, line, 2)
        password, stored = args
        if not isinstance(password, str):
            raise RuntimeErr(f"password_verify() expects a string password, got {type_name(password)}", line)
        if not isinstance(stored, str):
            raise RuntimeErr(f"password_verify() expects a string hash, got {type_name(stored)}", line)
        try:
            algo, iterations_text, salt_hex, digest_hex = stored.split("$")
            if algo != "pbkdf2_sha256":
                return False
            iterations = int(iterations_text)
            salt = binascii.unhexlify(salt_hex)
            expected = binascii.unhexlify(digest_hex)
        except (ValueError, binascii.Error):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    def b_random(args, line):
        import random as _random

        _arity("random", args, line, 0)
        return _random.random()

    def b_random_int(args, line):
        import random as _random

        _arity("random_int", args, line, 2)
        lo = int(_require_number("random_int", args[0], line))
        hi = int(_require_number("random_int", args[1], line))
        return _random.randint(lo, hi)

    def b_random_choice(args, line):
        import random as _random

        _arity("random_choice", args, line, 1)
        lst = _require_list("random_choice", args[0], line)
        if not lst:
            raise RuntimeErr("random_choice() on an empty list", line)
        return _random.choice(lst)

    def b_shuffle(args, line):
        import random as _random

        _arity("shuffle", args, line, 1)
        lst = list(_require_list("shuffle", args[0], line))
        _random.shuffle(lst)
        return lst

    def b_all(args, line):
        from quill.values import is_truthy

        _arity("all", args, line, 1)
        lst = _require_list("all", args[0], line)
        return all(is_truthy(x) for x in lst)

    def b_any(args, line):
        from quill.values import is_truthy

        _arity("any", args, line, 1)
        lst = _require_list("any", args[0], line)
        return any(is_truthy(x) for x in lst)

    def b_chr(args, line):
        _arity("chr", args, line, 1)
        n = int(_require_number("chr", args[0], line))
        try:
            return chr(n)
        except (ValueError, OverflowError):
            raise RuntimeErr(f"chr() arg {n} is not a valid character code", line)

    def b_ord(args, line):
        _arity("ord", args, line, 1)
        s = args[0]
        if not isinstance(s, str) or len(s) != 1:
            raise RuntimeErr("ord() expects a single-character string", line)
        return ord(s)

    def b_hex(args, line):
        _arity("hex", args, line, 1)
        return hex(int(_require_number("hex", args[0], line)))

    def b_oct(args, line):
        _arity("oct", args, line, 1)
        return oct(int(_require_number("oct", args[0], line)))

    def b_bin(args, line):
        _arity("bin", args, line, 1)
        return bin(int(_require_number("bin", args[0], line)))

    def b_pow(args, line):
        _arity("pow", args, line, 2, 3)
        base = _require_number("pow", args[0], line)
        exponent = _require_number("pow", args[1], line)
        if len(args) == 3:
            modulus = _require_number("pow", args[2], line)
            if modulus == 0:
                raise RuntimeErr("pow() with modulus 0", line)
            return pow(int(base), int(exponent), int(modulus))
        return base**exponent

    def b_divmod(args, line):
        _arity("divmod", args, line, 2)
        a = _require_number("divmod", args[0], line)
        b = _require_number("divmod", args[1], line)
        if b == 0:
            raise RuntimeErr("divmod() by zero", line)
        quotient, remainder = divmod(a, b)
        return [quotient, remainder]

    def b_repr(args, line):
        from quill.values import quill_repr

        _arity("repr", args, line, 1)
        return quill_repr(args[0])

    def b_log(args, line):
        import math

        _arity("log", args, line, 1, 2)
        n = _require_number("log", args[0], line)
        if n <= 0:
            raise RuntimeErr("log() of a non-positive number", line)
        if len(args) == 2:
            base = _require_number("log", args[1], line)
            return math.log(n, base)
        return math.log(n)

    def b_exp(args, line):
        import math

        _arity("exp", args, line, 1)
        return math.exp(_require_number("exp", args[0], line))

    def b_sin(args, line):
        import math

        _arity("sin", args, line, 1)
        return math.sin(_require_number("sin", args[0], line))

    def b_cos(args, line):
        import math

        _arity("cos", args, line, 1)
        return math.cos(_require_number("cos", args[0], line))

    def b_tan(args, line):
        import math

        _arity("tan", args, line, 1)
        return math.tan(_require_number("tan", args[0], line))

    def b_gcd(args, line):
        import math

        _arity("gcd", args, line, 2)
        a = int(_require_number("gcd", args[0], line))
        b = int(_require_number("gcd", args[1], line))
        return math.gcd(a, b)

    def b_map(args, line):
        from quill.interpreter import CURRENT_INTERPRETER

        _arity("map", args, line, 2)
        fn, lst = args
        lst = _require_list("map", lst, line)
        return [CURRENT_INTERPRETER[0].call(fn, [x], line) for x in lst]

    def b_filter(args, line):
        from quill.interpreter import CURRENT_INTERPRETER
        from quill.values import is_truthy

        _arity("filter", args, line, 2)
        fn, lst = args
        lst = _require_list("filter", lst, line)
        return [x for x in lst if is_truthy(CURRENT_INTERPRETER[0].call(fn, [x], line))]

    def b_reduce(args, line):
        from quill.interpreter import CURRENT_INTERPRETER

        _arity("reduce", args, line, 3)
        fn, lst, init = args
        lst = _require_list("reduce", lst, line)
        acc = init
        for x in lst:
            acc = CURRENT_INTERPRETER[0].call(fn, [acc, x], line)
        return acc

    def _compile_regex(pattern, line):
        import re

        try:
            return re.compile(pattern)
        except re.error as exc:
            raise RuntimeErr(f"invalid regex pattern: {exc}", line)

    def _require_two_strings(name, args, line):
        pattern, text = args
        if not isinstance(pattern, str):
            raise RuntimeErr(f"{name}() expects a string pattern, got {type_name(pattern)}", line)
        if not isinstance(text, str):
            raise RuntimeErr(f"{name}() expects a string, got {type_name(text)}", line)
        return pattern, text

    def b_regex_match(args, line):
        _arity("regex_match", args, line, 2)
        pattern, text = _require_two_strings("regex_match", args, line)
        return _compile_regex(pattern, line).search(text) is not None

    def b_regex_find(args, line):
        _arity("regex_find", args, line, 2)
        pattern, text = _require_two_strings("regex_find", args, line)
        m = _compile_regex(pattern, line).search(text)
        return m.group(0) if m else None

    def b_regex_find_all(args, line):
        _arity("regex_find_all", args, line, 2)
        pattern, text = _require_two_strings("regex_find_all", args, line)
        return [m.group(0) for m in _compile_regex(pattern, line).finditer(text)]

    def b_regex_replace(args, line):
        _arity("regex_replace", args, line, 3)
        pattern, text = _require_two_strings("regex_replace", args[:2], line)
        repl = args[2]
        if not isinstance(repl, str):
            raise RuntimeErr("regex_replace() replacement must be a string", line)
        return _compile_regex(pattern, line).sub(repl, text)

    def b_regex_split(args, line):
        _arity("regex_split", args, line, 2)
        pattern, text = _require_two_strings("regex_split", args, line)
        return _compile_regex(pattern, line).split(text)

    def b_regex_groups(args, line):
        _arity("regex_groups", args, line, 2)
        pattern, text = _require_two_strings("regex_groups", args, line)
        m = _compile_regex(pattern, line).search(text)
        return list(m.groups()) if m else None

    def b_time(args, line):
        import time as _time

        _arity("time", args, line, 0)
        return _time.time()

    def b_sleep(args, line):
        import time as _time

        _arity("sleep", args, line, 1)
        seconds = _require_number("sleep", args[0], line)
        if seconds < 0:
            raise RuntimeErr("sleep() duration must not be negative", line)
        _time.sleep(seconds)
        return None

    def b_uuid(args, line):
        import uuid as _uuid

        _arity("uuid", args, line, 0)
        return str(_uuid.uuid4())

    def b_base64_encode(args, line):
        import base64

        _arity("base64_encode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"base64_encode() expects a string, got {type_name(text)}", line)
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    def b_base64_decode(args, line):
        import base64
        import binascii

        _arity("base64_decode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"base64_decode() expects a string, got {type_name(text)}", line)
        try:
            return base64.b64decode(text, validate=True).decode("utf-8", errors="replace")
        except (binascii.Error, ValueError):
            raise RuntimeErr("invalid base64 input", line)

    def b_list_dir(args, line):
        import os

        _arity("list_dir", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"list_dir() expects a string path, got {type_name(path)}", line)
        try:
            return sorted(os.listdir(path))
        except OSError as exc:
            raise RuntimeErr(f"cannot list '{path}': {exc.strerror}", line)

    def b_make_dir(args, line):
        import os

        _arity("make_dir", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"make_dir() expects a string path, got {type_name(path)}", line)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as exc:
            raise RuntimeErr(f"cannot create '{path}': {exc.strerror}", line)
        return None

    def b_delete_file(args, line):
        import os

        _arity("delete_file", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"delete_file() expects a string path, got {type_name(path)}", line)
        try:
            os.remove(path)
        except OSError as exc:
            raise RuntimeErr(f"cannot delete '{path}': {exc.strerror}", line)
        return None

    def b_path_join(args, line):
        import os

        _arity("path_join", args, line, 1)
        parts = args[0]
        if not isinstance(parts, list) or not all(isinstance(p, str) for p in parts):
            raise RuntimeErr("path_join() expects a list of strings", line)
        if not parts:
            raise RuntimeErr("path_join() needs at least one path segment", line)
        return os.path.join(*parts)

    def b_cwd(args, line):
        import os

        _arity("cwd", args, line, 0)
        return os.getcwd()

    def b_atan(args, line):
        import math

        _arity("atan", args, line, 1)
        return math.atan(_require_number("atan", args[0], line))

    def b_atan2(args, line):
        import math

        _arity("atan2", args, line, 2)
        y = _require_number("atan2", args[0], line)
        x = _require_number("atan2", args[1], line)
        return math.atan2(y, x)

    def b_log2(args, line):
        import math

        _arity("log2", args, line, 1)
        n = _require_number("log2", args[0], line)
        if n <= 0:
            raise RuntimeErr("log2() of a non-positive number", line)
        return math.log2(n)

    def b_log10(args, line):
        import math

        _arity("log10", args, line, 1)
        n = _require_number("log10", args[0], line)
        if n <= 0:
            raise RuntimeErr("log10() of a non-positive number", line)
        return math.log10(n)

    def b_degrees(args, line):
        import math

        _arity("degrees", args, line, 1)
        return math.degrees(_require_number("degrees", args[0], line))

    def b_radians(args, line):
        import math

        _arity("radians", args, line, 1)
        return math.radians(_require_number("radians", args[0], line))

    def b_hypot(args, line):
        import math

        _arity("hypot", args, line, 2)
        x = _require_number("hypot", args[0], line)
        y = _require_number("hypot", args[1], line)
        return math.hypot(x, y)

    def b_factorial(args, line):
        import math

        _arity("factorial", args, line, 1)
        n = _require_number("factorial", args[0], line)
        if n < 0 or n != int(n):
            raise RuntimeErr("factorial() expects a non-negative whole number", line)
        return math.factorial(int(n))

    def b_assert(args, line):
        from quill.values import is_truthy

        _arity("assert", args, line, 1, 2)
        if not is_truthy(args[0]):
            message = quill_str(args[1]) if len(args) == 2 else "assertion failed"
            raise RuntimeErr(message, line)
        return None

    def b_exit(args, line):
        import sys

        _arity("exit", args, line, 0, 1)
        code = int(_require_number("exit", args[0], line)) if args else 0
        sys.exit(code)

    def b_deep_copy(args, line):
        _arity("deep_copy", args, line, 1)

        def _copy(v):
            if isinstance(v, list):
                return [_copy(x) for x in v]
            if isinstance(v, dict):
                return {k: _copy(x) for k, x in v.items()}
            return v  # numbers/strings/bools/nil are immutable; instances are shared, not cloned

        return _copy(args[0])

    def b_url_decode(args, line):
        import urllib.parse

        _arity("url_decode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"url_decode() expects a string, got {type_name(text)}", line)
        return urllib.parse.unquote(text)

    def b_html_escape(args, line):
        import html

        _arity("html_escape", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"html_escape() expects a string, got {type_name(text)}", line)
        return html.escape(text)

    def b_html_unescape(args, line):
        import html

        _arity("html_unescape", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"html_unescape() expects a string, got {type_name(text)}", line)
        return html.unescape(text)

    def b_csv_parse(args, line):
        import csv
        import io

        _arity("csv_parse", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"csv_parse() expects a string, got {type_name(text)}", line)
        try:
            return [list(row) for row in csv.reader(io.StringIO(text))]
        except csv.Error as exc:
            raise RuntimeErr(f"invalid CSV: {exc}", line)

    def b_csv_stringify(args, line):
        import csv
        import io

        _arity("csv_stringify", args, line, 1)
        rows = args[0]
        if not isinstance(rows, list) or not all(isinstance(r, list) for r in rows):
            raise RuntimeErr("csv_stringify() expects a list of lists", line)
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        for row in rows:
            writer.writerow([quill_str(v) for v in row])
        return buf.getvalue()

    def b_bit_and(args, line):
        _arity("bit_and", args, line, 2)
        a = int(_require_number("bit_and", args[0], line))
        b = int(_require_number("bit_and", args[1], line))
        return a & b

    def b_bit_or(args, line):
        _arity("bit_or", args, line, 2)
        a = int(_require_number("bit_or", args[0], line))
        b = int(_require_number("bit_or", args[1], line))
        return a | b

    def b_bit_xor(args, line):
        _arity("bit_xor", args, line, 2)
        a = int(_require_number("bit_xor", args[0], line))
        b = int(_require_number("bit_xor", args[1], line))
        return a ^ b

    def b_bit_not(args, line):
        _arity("bit_not", args, line, 1)
        return ~int(_require_number("bit_not", args[0], line))

    def b_bit_shift_left(args, line):
        _arity("bit_shift_left", args, line, 2)
        a = int(_require_number("bit_shift_left", args[0], line))
        n = int(_require_number("bit_shift_left", args[1], line))
        if n < 0:
            raise RuntimeErr("bit_shift_left() shift amount must not be negative", line)
        return a << n

    def b_bit_shift_right(args, line):
        _arity("bit_shift_right", args, line, 2)
        a = int(_require_number("bit_shift_right", args[0], line))
        n = int(_require_number("bit_shift_right", args[1], line))
        if n < 0:
            raise RuntimeErr("bit_shift_right() shift amount must not be negative", line)
        return a >> n

    def b_is_number(args, line):
        _arity("is_number", args, line, 1)
        return type_name(args[0]) == "number"

    def b_is_string(args, line):
        _arity("is_string", args, line, 1)
        return type_name(args[0]) == "string"

    def b_is_list(args, line):
        _arity("is_list", args, line, 1)
        return type_name(args[0]) == "list"

    def b_is_map(args, line):
        _arity("is_map", args, line, 1)
        return type_name(args[0]) == "map"

    def b_is_bool(args, line):
        _arity("is_bool", args, line, 1)
        return type_name(args[0]) == "bool"

    def b_is_nil(args, line):
        _arity("is_nil", args, line, 1)
        return args[0] is None

    def b_is_function(args, line):
        _arity("is_function", args, line, 1)
        return type_name(args[0]) == "function"

    def b_is_class(args, line):
        from quill.values import QuillClass

        _arity("is_class", args, line, 1)
        return isinstance(args[0], QuillClass)

    def b_mean(args, line):
        import statistics

        _arity("mean", args, line, 1)
        lst = _require_list("mean", args[0], line)
        if not lst:
            raise RuntimeErr("mean() on an empty list", line)
        return statistics.mean(lst)

    def b_median(args, line):
        import statistics

        _arity("median", args, line, 1)
        lst = _require_list("median", args[0], line)
        if not lst:
            raise RuntimeErr("median() on an empty list", line)
        return statistics.median(lst)

    def b_mode(args, line):
        import statistics

        _arity("mode", args, line, 1)
        lst = _require_list("mode", args[0], line)
        if not lst:
            raise RuntimeErr("mode() on an empty list", line)
        return statistics.mode(lst)

    def b_variance(args, line):
        import statistics

        _arity("variance", args, line, 1)
        lst = _require_list("variance", args[0], line)
        if len(lst) < 2:
            raise RuntimeErr("variance() needs at least 2 values", line)
        return statistics.variance(lst)

    def b_stdev(args, line):
        import statistics

        _arity("stdev", args, line, 1)
        lst = _require_list("stdev", args[0], line)
        if len(lst) < 2:
            raise RuntimeErr("stdev() needs at least 2 values", line)
        return statistics.stdev(lst)

    def b_percentile(args, line):
        _arity("percentile", args, line, 2)
        lst = _require_list("percentile", args[0], line)
        p = _require_number("percentile", args[1], line)
        if not lst:
            raise RuntimeErr("percentile() on an empty list", line)
        if not (0 <= p <= 100):
            raise RuntimeErr("percentile() expects p between 0 and 100", line)
        data = sorted(lst)
        k = (len(data) - 1) * (p / 100)
        f = int(k)
        c = min(f + 1, len(data) - 1)
        if f == c:
            return data[f]
        return data[f] * (c - k) + data[c] * (k - f)

    def b_date_format(args, line):
        import time as _time

        _arity("date_format", args, line, 2)
        ts = _require_number("date_format", args[0], line)
        fmt = args[1]
        if not isinstance(fmt, str):
            raise RuntimeErr("date_format() expects a string format", line)
        try:
            return _time.strftime(fmt, _time.localtime(ts))
        except (ValueError, OSError) as exc:
            raise RuntimeErr(f"date_format() failed: {exc}", line)

    def b_date_parse(args, line):
        import time as _time

        _arity("date_parse", args, line, 2)
        text, fmt = args
        if not isinstance(text, str):
            raise RuntimeErr(f"date_parse() expects a string, got {type_name(text)}", line)
        if not isinstance(fmt, str):
            raise RuntimeErr(f"date_parse() expects a string format, got {type_name(fmt)}", line)
        try:
            return _time.mktime(_time.strptime(text, fmt))
        except ValueError as exc:
            raise RuntimeErr(f"date_parse() failed: {exc}", line)

    def b_clamp(args, line):
        _arity("clamp", args, line, 3)
        n = _require_number("clamp", args[0], line)
        lo = _require_number("clamp", args[1], line)
        hi = _require_number("clamp", args[2], line)
        if lo > hi:
            raise RuntimeErr("clamp() needs lo <= hi", line)
        return max(lo, min(n, hi))

    def b_lerp(args, line):
        _arity("lerp", args, line, 3)
        a = _require_number("lerp", args[0], line)
        b = _require_number("lerp", args[1], line)
        t = _require_number("lerp", args[2], line)
        return a + (b - a) * t

    def b_sign(args, line):
        _arity("sign", args, line, 1)
        n = _require_number("sign", args[0], line)
        return (n > 0) - (n < 0)

    def b_is_even(args, line):
        _arity("is_even", args, line, 1)
        n = _require_number("is_even", args[0], line)
        if n != int(n):
            raise RuntimeErr("is_even() expects a whole number", line)
        return int(n) % 2 == 0

    def b_is_odd(args, line):
        _arity("is_odd", args, line, 1)
        n = _require_number("is_odd", args[0], line)
        if n != int(n):
            raise RuntimeErr("is_odd() expects a whole number", line)
        return int(n) % 2 != 0

    def b_hex_encode(args, line):
        _arity("hex_encode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"hex_encode() expects a string, got {type_name(text)}", line)
        return text.encode("utf-8").hex()

    def b_hex_decode(args, line):
        import binascii

        _arity("hex_decode", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"hex_decode() expects a string, got {type_name(text)}", line)
        try:
            return bytes.fromhex(text).decode("utf-8", errors="replace")
        except (ValueError, binascii.Error):
            raise RuntimeErr("invalid hex input", line)

    def b_md5(args, line):
        import hashlib

        _arity("md5", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"md5() expects a string, got {type_name(text)}", line)
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def b_sha1(args, line):
        import hashlib

        _arity("sha1", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"sha1() expects a string, got {type_name(text)}", line)
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def b_sha512(args, line):
        import hashlib

        _arity("sha512", args, line, 1)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"sha512() expects a string, got {type_name(text)}", line)
        return hashlib.sha512(text.encode("utf-8")).hexdigest()

    def b_hmac_sha256(args, line):
        import hashlib
        import hmac as _hmac

        _arity("hmac_sha256", args, line, 2)
        key, message = args
        if not isinstance(key, str):
            raise RuntimeErr(f"hmac_sha256() expects a string key, got {type_name(key)}", line)
        if not isinstance(message, str):
            raise RuntimeErr(f"hmac_sha256() expects a string message, got {type_name(message)}", line)
        return _hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    def b_args(args, line):
        _arity("args", args, line, 0)
        return list(script_args or [])

    def b_platform(args, line):
        import platform as _platform

        _arity("platform", args, line, 0)
        return _platform.system()

    def b_text_wrap(args, line):
        import textwrap

        _arity("text_wrap", args, line, 2)
        text = args[0]
        if not isinstance(text, str):
            raise RuntimeErr(f"text_wrap() expects a string, got {type_name(text)}", line)
        width = int(_require_number("text_wrap", args[1], line))
        if width < 1:
            raise RuntimeErr("text_wrap() width must be at least 1", line)
        return textwrap.wrap(text, width)

    def b_sample(args, line):
        import random as _random

        _arity("sample", args, line, 2)
        lst = _require_list("sample", args[0], line)
        n = int(_require_number("sample", args[1], line))
        if n < 0 or n > len(lst):
            raise RuntimeErr(f"sample() size must be between 0 and {len(lst)}", line)
        return _random.sample(lst, n)

    def b_copy_file(args, line):
        import shutil

        _arity("copy_file", args, line, 2)
        src, dst = args
        if not isinstance(src, str):
            raise RuntimeErr(f"copy_file() expects a string source path, got {type_name(src)}", line)
        if not isinstance(dst, str):
            raise RuntimeErr(f"copy_file() expects a string destination path, got {type_name(dst)}", line)
        try:
            shutil.copy(src, dst)
        except OSError as exc:
            raise RuntimeErr(f"cannot copy '{src}' to '{dst}': {exc.strerror}", line)
        return None

    def b_move_file(args, line):
        import shutil

        _arity("move_file", args, line, 2)
        src, dst = args
        if not isinstance(src, str):
            raise RuntimeErr(f"move_file() expects a string source path, got {type_name(src)}", line)
        if not isinstance(dst, str):
            raise RuntimeErr(f"move_file() expects a string destination path, got {type_name(dst)}", line)
        try:
            shutil.move(src, dst)
        except OSError as exc:
            raise RuntimeErr(f"cannot move '{src}' to '{dst}': {exc.strerror}", line)
        return None

    def b_file_size(args, line):
        import os

        _arity("file_size", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"file_size() expects a string path, got {type_name(path)}", line)
        try:
            return os.path.getsize(path)
        except OSError as exc:
            raise RuntimeErr(f"cannot stat '{path}': {exc.strerror}", line)

    def b_delete_dir(args, line):
        import shutil

        _arity("delete_dir", args, line, 1)
        path = args[0]
        if not isinstance(path, str):
            raise RuntimeErr(f"delete_dir() expects a string path, got {type_name(path)}", line)
        try:
            shutil.rmtree(path)
        except OSError as exc:
            raise RuntimeErr(f"cannot delete '{path}': {exc.strerror}", line)
        return None

    def b_env_all(args, line):
        import os

        _arity("env_all", args, line, 0)
        return dict(os.environ)

    def b_levenshtein(args, line):
        _arity("levenshtein", args, line, 2)
        a, b = args
        if not isinstance(a, str):
            raise RuntimeErr(f"levenshtein() expects a string, got {type_name(a)}", line)
        if not isinstance(b, str):
            raise RuntimeErr(f"levenshtein() expects a string, got {type_name(b)}", line)
        if len(a) < len(b):
            a, b = b, a
        if not b:
            return len(a)
        previous_row = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            current_row = [i + 1]
            for j, cb in enumerate(b):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (ca != cb)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def b_env_get(args, line):
        import os

        _arity("env_get", args, line, 1, 2)
        name = args[0]
        if not isinstance(name, str):
            raise RuntimeErr(f"env_get() expects a string name, got {type_name(name)}", line)
        default = args[1] if len(args) == 2 else None
        return os.environ.get(name, default)

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
    reg("json_encode", b_json_encode)
    reg("json_decode", b_json_decode)
    reg("sha256", b_sha256)
    reg("password_hash", b_password_hash)
    reg("password_verify", b_password_verify)
    reg("random", b_random)
    reg("random_int", b_random_int)
    reg("random_choice", b_random_choice)
    reg("shuffle", b_shuffle)
    reg("env_get", b_env_get)
    reg("http_get", b_http_get)
    reg("http_post", b_http_post)
    reg("all", b_all)
    reg("any", b_any)
    reg("chr", b_chr)
    reg("ord", b_ord)
    reg("hex", b_hex)
    reg("oct", b_oct)
    reg("bin", b_bin)
    reg("pow", b_pow)
    reg("divmod", b_divmod)
    reg("repr", b_repr)
    reg("log", b_log)
    reg("exp", b_exp)
    reg("sin", b_sin)
    reg("cos", b_cos)
    reg("tan", b_tan)
    reg("gcd", b_gcd)
    reg("map", b_map)
    reg("filter", b_filter)
    reg("reduce", b_reduce)
    reg("regex_match", b_regex_match)
    reg("regex_find", b_regex_find)
    reg("regex_find_all", b_regex_find_all)
    reg("regex_replace", b_regex_replace)
    reg("regex_split", b_regex_split)
    reg("regex_groups", b_regex_groups)
    reg("time", b_time)
    reg("sleep", b_sleep)
    reg("uuid", b_uuid)
    reg("base64_encode", b_base64_encode)
    reg("base64_decode", b_base64_decode)
    reg("list_dir", b_list_dir)
    reg("make_dir", b_make_dir)
    reg("delete_file", b_delete_file)
    reg("path_join", b_path_join)
    reg("cwd", b_cwd)
    reg("atan", b_atan)
    reg("atan2", b_atan2)
    reg("log2", b_log2)
    reg("log10", b_log10)
    reg("degrees", b_degrees)
    reg("radians", b_radians)
    reg("hypot", b_hypot)
    reg("factorial", b_factorial)
    reg("assert", b_assert)
    reg("exit", b_exit)
    reg("deep_copy", b_deep_copy)
    reg("url_decode", b_url_decode)
    reg("html_escape", b_html_escape)
    reg("html_unescape", b_html_unescape)
    reg("csv_parse", b_csv_parse)
    reg("csv_stringify", b_csv_stringify)
    reg("bit_and", b_bit_and)
    reg("bit_or", b_bit_or)
    reg("bit_xor", b_bit_xor)
    reg("bit_not", b_bit_not)
    reg("bit_shift_left", b_bit_shift_left)
    reg("bit_shift_right", b_bit_shift_right)
    reg("is_number", b_is_number)
    reg("is_string", b_is_string)
    reg("is_list", b_is_list)
    reg("is_map", b_is_map)
    reg("is_bool", b_is_bool)
    reg("is_nil", b_is_nil)
    reg("is_function", b_is_function)
    reg("is_class", b_is_class)
    reg("mean", b_mean)
    reg("median", b_median)
    reg("mode", b_mode)
    reg("variance", b_variance)
    reg("stdev", b_stdev)
    reg("percentile", b_percentile)
    reg("date_format", b_date_format)
    reg("date_parse", b_date_parse)
    reg("clamp", b_clamp)
    reg("lerp", b_lerp)
    reg("sign", b_sign)
    reg("is_even", b_is_even)
    reg("is_odd", b_is_odd)
    reg("hex_encode", b_hex_encode)
    reg("hex_decode", b_hex_decode)
    reg("md5", b_md5)
    reg("sha1", b_sha1)
    reg("sha512", b_sha512)
    reg("hmac_sha256", b_hmac_sha256)
    reg("args", b_args)
    reg("platform", b_platform)
    reg("text_wrap", b_text_wrap)
    reg("sample", b_sample)
    reg("copy_file", b_copy_file)
    reg("move_file", b_move_file)
    reg("file_size", b_file_size)
    reg("delete_dir", b_delete_dir)
    reg("env_all", b_env_all)
    reg("levenshtein", b_levenshtein)
    env.declare("PI", 3.141592653589793)
    env.declare("E", 2.718281828459045)
    env.declare("INF", float("inf"))
    env.declare("NAN", float("nan"))
    env.declare("TAU", 6.283185307179586)

    return env
