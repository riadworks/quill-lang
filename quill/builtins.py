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
        if not isinstance(password, str) or not isinstance(stored, str):
            raise RuntimeErr("password_verify() expects two strings", line)
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
    env.declare("PI", 3.141592653589793)
    env.declare("E", 2.718281828459045)

    return env
