import pytest

from tests.helpers import run, run_expect_error


def test_class_basic_fields_and_methods():
    out = run(
        "class Point:\n"
        "    pull init(x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "    pull to_string():\n"
        '        return f"({self.x}, {self.y})"\n'
        "let p = Point(1, 2)\n"
        "print(p.x)\n"
        "print(p.to_string())\n"
    )
    assert out == "1\n(1, 2)\n"


def test_class_inheritance_and_super():
    out = run(
        "class Animal:\n"
        "    pull init(name):\n"
        "        self.name = name\n"
        "    pull speak():\n"
        '        return f"{self.name} makes a sound"\n'
        "class Dog(Animal):\n"
        "    pull init(name, breed):\n"
        "        super.init(name)\n"
        "        self.breed = breed\n"
        "    pull speak():\n"
        '        return f"{self.name} the {self.breed} barks"\n'
        'let a = Animal("Creature")\n'
        'let d = Dog("Rex", "Lab")\n'
        "print(a.speak())\n"
        "print(d.speak())\n"
        "print(type(d))\n"
    )
    assert out == "Creature makes a sound\nRex the Lab barks\nDog\n"


def test_three_level_inheritance_super_chain():
    # regression test: super must resolve against the *defining* class of the
    # current method, not the runtime instance's concrete class, or a 3-level
    # chain loops instead of climbing to the top.
    out = run(
        "class A:\n"
        "    pull tag():\n"
        '        return "A"\n'
        "class B(A):\n"
        "    pull tag():\n"
        '        return super.tag() + "B"\n'
        "class C(B):\n"
        "    pull tag():\n"
        '        return super.tag() + "C"\n'
        "print(C().tag())\n"
    )
    assert out == "ABC\n"


def test_class_wrong_init_arity_error():
    msg = run_expect_error(
        "class Point:\n"
        "    pull init(x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "Point(1)\n"
    )
    assert "expects 2 argument" in msg


def test_class_unknown_field_error():
    msg = run_expect_error(
        "class Point:\n"
        "    pull init(x):\n"
        "        self.x = x\n"
        "let p = Point(1)\n"
        "print(p.y)\n"
    )
    assert "has no field or method" in msg


def test_try_except_catches_raise():
    out = run('try:\n    raise "boom"\nexcept e:\n    print(f"caught {e}")\n')
    assert out == "caught boom\n"


def test_try_except_catches_runtime_error():
    out = run("try:\n    let x = 1 / 0\nexcept e:\n    print(e)\n")
    assert out == "division by zero\n"


def test_try_finally_runs_on_success_and_failure():
    out = run(
        "try:\n"
        '    print("body")\n'
        "finally:\n"
        '    print("cleanup")\n'
        "try:\n"
        '    raise "x"\n'
        "except e:\n"
        '    print("caught")\n'
        "finally:\n"
        '    print("cleanup2")\n'
    )
    assert out == "body\ncleanup\ncaught\ncleanup2\n"


def test_try_finally_runs_before_return_propagates():
    out = run(
        "pull f():\n"
        "    try:\n"
        '        return "value"\n'
        "    finally:\n"
        '        print("finally ran")\n'
        "print(f())\n"
    )
    assert out == "finally ran\nvalue\n"


def test_uncaught_exception_without_except_clause_propagates():
    msg = run_expect_error("try:\n    raise \"oops\"\nfinally:\n    let pass_marker = 1\n")
    assert "oops" in msg


def test_string_methods():
    out = run(
        '  print("  Hi  ".trim())\n'
        '  print("Hi".upper())\n'
        '  print("Hi".lower())\n'
        '  print("a,b,c".split(","))\n'
        '  print("abc".replace("b", "X"))\n'
        '  print("abc".contains("b"))\n'
        '  print("abc".starts_with("ab"))\n'
        '  print("abc".ends_with("bc"))\n'
        '  print("abc".find("c"))\n'
        '  print("ab".repeat(2))\n'.replace("  ", "")
    )
    assert out == 'Hi\nHI\nhi\n["a", "b", "c"]\naXc\ntrue\ntrue\ntrue\n2\nabab\n'


def test_list_methods():
    out = run(
        "let xs = [3, 1, 2]\n"
        "print(xs.sort())\n"
        "print(xs.reverse())\n"
        "print(xs.contains(2))\n"
        "print(xs.index_of(2))\n"
        'print(xs.join("-"))\n'
        "print(xs.map(pull(x): return x + 1))\n"
        "print(xs.filter(pull(x): return x > 1))\n"
        "print(xs.reduce(pull(a, b): return a + b, 0))\n"
        "xs.push(99)\n"
        "print(xs)\n"
        "print(xs.pop())\n"
    )
    # sort()/reverse() are non-mutating (return a new list, like the standalone
    # sorted() builtin) - xs itself stays [3, 1, 2] throughout except for push/pop.
    assert out == (
        "[1, 2, 3]\n[2, 1, 3]\ntrue\n2\n3-1-2\n[4, 2, 3]\n[3, 2]\n6\n[3, 1, 2, 99]\n99\n"
    )


def test_map_methods():
    out = run(
        'let m = {"a": 1, "b": 2}\n'
        'print(m.keys())\nprint(m.values())\nprint(m.items())\n'
        'print(m.has("a"))\nprint(m.get("z", -1))\n'
    )
    assert out == '["a", "b"]\n[1, 2]\n[["a", 1], ["b", 2]]\ntrue\n-1\n'


def test_ternary_expression():
    out = run('let x = 10\nprint("even" if x % 2 == 0 else "odd")\n')
    assert out == "even\n"


def test_augmented_assignment():
    out = run("let x = 5\nx += 3\nx *= 2\nx -= 1\nx /= 5\nprint(x)\n")
    # / always produces a float (15.0 / 5 = 3.0), but whole-number floats print
    # without a trailing .0 by design - see test_math_builtins for the same rule.
    assert out == "3\n"


def test_floor_division():
    out = run("print(7 // 2)\nprint(-7 // 2)\n")
    assert out == "3\n-4\n"


def test_math_builtins():
    out = run("print(sqrt(16))\nprint(floor(3.9))\nprint(ceil(3.1))\nprint(PI > 3.1 and PI < 3.2)\n")
    assert out == "4\n3\n4\ntrue\n"


def test_higher_order_via_list_map_matches_manual_loop():
    out = run(
        "pull double(x):\n"
        "    return x * 2\n"
        "print([1, 2, 3].map(double))\n"
    )
    assert out == "[2, 4, 6]\n"


def test_file_io_roundtrip(tmp_path):
    from quill.builtins import build_globals
    from quill.interpreter import Interpreter
    from quill.lexer import tokenize
    from quill.parser import parse

    target = str(tmp_path / "out.txt").replace("\\", "\\\\")
    source = (
        f'write_file("{target}", "hello quill")\n'
        f'print(file_exists("{target}"))\n'
        f'print(read_file("{target}"))\n'
    )
    env = build_globals()
    interp = Interpreter(env)
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(parse(tokenize(source)))
    assert buf.getvalue() == "true\nhello quill\n"


def test_import_module(tmp_path):
    from quill.builtins import build_globals
    from quill.interpreter import Interpreter
    from quill.lexer import tokenize
    from quill.parser import parse

    (tmp_path / "mod.ql").write_text('let GREETING = "hi"\npull shout(s):\n    return s.upper()\n', encoding="utf-8")
    main_source = 'import "mod.ql" as mod\nprint(mod.GREETING)\nprint(mod.shout("yo"))\n'

    env = build_globals()
    interp = Interpreter(env)
    interp.current_dir = str(tmp_path)
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(parse(tokenize(main_source)))
    assert buf.getvalue() == "hi\nYO\n"


def test_single_line_block_form():
    out = run("let x = 5\nif x > 0: print(\"positive\")\nelse: print(\"non-positive\")\n")
    assert out == "positive\n"


def test_list_pop_with_index():
    out = run('let xs = [10, 20, 30]\nprint(xs.pop(0))\nprint(xs)\nprint(xs.pop(-1))\nprint(xs)\n')
    assert out == "10\n[20, 30]\n30\n[20]\n"


def test_list_pop_index_out_of_range_error():
    msg = run_expect_error("let xs = [1, 2]\nxs.pop(5)\n")
    assert "out of range" in msg


def test_fstring_escaped_braces():
    # {{ and }} must produce literal braces without triggering interpolation -
    # found missing while generating CSS (e.g. "body {{ color: red }}") inside
    # an f-string for the website app; a real gap, not just that app's problem.
    out = run('let x = 5\nprint(f"{{literal}} and {x} and {{another}}")\n')
    assert out == "{literal} and 5 and {another}\n"


def test_fstring_lone_closing_brace_is_an_error():
    msg = run_expect_error('print(f"oops }")\n')
    assert "single" in msg and "}" in msg


def test_plain_string_still_allows_unescaped_braces():
    out = run('print("a { b } c")\n')
    assert out == "a { b } c\n"


def test_input_strips_leading_bom(monkeypatch):
    # Some Windows terminals/pipes (e.g. PowerShell piping a here-string into
    # stdin) prepend a UTF-8 BOM to the very first line of input, which would
    # otherwise silently break the first input()-based == comparison in any
    # interactive program - found while building and testing apps/tasks.
    monkeypatch.setattr("builtins.input", lambda prompt="": "﻿1")
    out = run('let choice = input("> ")\nprint(choice == "1")\n')
    assert out == "true\n"


def test_list_comprehension_basic_and_filtered():
    out = run(
        "let nums = [1, 2, 3, 4, 5]\n"
        "print([x * x for x in nums])\n"
        "print([x for x in nums if x % 2 == 0])\n"
    )
    assert out == "[1, 4, 9, 16, 25]\n[2, 4]\n"


def test_list_comprehension_with_ternary_output_expr():
    # the ternary's own `if ... else ...` must not be confused with the
    # comprehension's filter `if` - disambiguated by parse order (the output
    # expression, ternary included, is fully parsed before checking for `for`).
    out = run("print([x if x % 2 == 0 else -x for x in [1, 2, 3, 4]])\n")
    assert out == "[-1, 2, -3, 4]\n"


def test_map_comprehension():
    out = run('print({x: x * x for x in [1, 2, 3] if x > 1})\n')
    assert out == "{2: 4, 3: 9}\n"


def test_multi_clause_comprehension_is_a_cartesian_product():
    out = run("print([[x, y] for x in [1, 2] for y in [10, 20]])\n")
    assert out == "[[1, 10], [1, 20], [2, 10], [2, 20]]\n"


def test_multi_clause_comprehension_with_filter_referencing_both_vars():
    out = run("print([x + y for x in [1, 2, 3] for y in [1, 2, 3] if x != y])\n")
    assert out == "[3, 4, 3, 5, 4, 5]\n"


def test_comprehension_scopes_loop_var_without_leaking():
    msg = run_expect_error("let sq = [x * x for x in [1, 2, 3]]\nprint(x)\n")
    assert "undefined variable" in msg


def test_let_destructuring():
    out = run("let pair = [1, 2]\nlet a, b = pair\nprint(a)\nprint(b)\n")
    assert out == "1\n2\n"


def test_bare_destructuring_assignment_can_swap():
    out = run("let a = 1\nlet b = 2\na, b = [b, a]\nprint(a)\nprint(b)\n")
    assert out == "2\n1\n"


def test_for_loop_destructuring_over_map_items():
    out = run('let m = {"x": 10, "y": 20}\nfor k, v in items(m):\n    print(f"{k}={v}")\n')
    assert out == "x=10\ny=20\n"


def test_for_loop_destructuring_over_list_of_pairs():
    out = run("for a, b in [[1, 2], [3, 4]]:\n    print(a + b)\n")
    assert out == "3\n7\n"


def test_destructuring_wrong_count_is_a_clear_error():
    msg = run_expect_error("let a, b, c = [1, 2]\n")
    assert "too few values to unpack" in msg
    assert "expected 3, got 2" in msg


def test_destructuring_non_list_is_a_clear_error():
    msg = run_expect_error("let a, b = 5\n")
    assert "cannot unpack" in msg


class _EchoHandler:
    """A minimal real HTTP server (stdlib http.server) used to test http_get/
    http_post against an actual socket, not a mock - the same way apps/website's
    serve() route tests worked."""

    @staticmethod
    def make():
        import http.server

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b'{"ok": true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                received = self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(received)))
                self.end_headers()
                self.wfile.write(received)

            def log_message(self, fmt, *args):
                pass

        return Handler


@pytest.fixture
def echo_server():
    import http.server
    import threading

    server = http.server.HTTPServer(("127.0.0.1", 0), _EchoHandler.make())
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield port
    server.shutdown()
    thread.join(timeout=2)


def test_http_get_against_a_real_server(echo_server):
    out = run(f'let r = http_get("http://127.0.0.1:{echo_server}/anything")\nprint(r["status"])\nprint(r["body"])\n')
    assert out == '200\n{"ok": true}\n'


def test_http_post_sends_form_encoded_body(echo_server):
    out = run(
        f'let r = http_post("http://127.0.0.1:{echo_server}/anything", {{"name": "Ada"}})\n'
        'print(r["status"])\nprint(r["body"])\n'
    )
    assert out == "200\nname=Ada\n"


def test_http_get_unreachable_host_is_a_clear_error():
    # port 1 on localhost should reliably refuse a connection rather than
    # timing out this test suite
    msg = run_expect_error('http_get("http://127.0.0.1:1/")\n')
    assert "http_get() failed" in msg


def test_fstring_interpolation_can_contain_a_double_quoted_string_argument():
    # A real trap found while building apps/adventure: Quill has no single-quote
    # strings, so writing xs.join(', ') (Python muscle memory) inside an
    # f-string's {expr} produces a bare, unrecognized ' when that raw fragment
    # is later re-tokenized on its own. The correct form - a double-quoted
    # string *inside* the interpolation - must still work, since the { }
    # extraction only tracks brace nesting and doesn't stop at quotes.
    out = run('let xs = ["a", "b", "c"]\nprint(f"{xs.join(", ")}")\n')
    assert out == "a, b, c\n"


VEC_CLASS = (
    "class Vec:\n"
    "    pull init(x, y):\n"
    "        self.x = x\n"
    "        self.y = y\n"
    "    pull __add__(other):\n"
    "        return Vec(self.x + other.x, self.y + other.y)\n"
    "    pull __sub__(other):\n"
    "        return Vec(self.x - other.x, self.y - other.y)\n"
    "    pull __mul__(scalar):\n"
    "        return Vec(self.x * scalar, self.y * scalar)\n"
    "    pull __eq__(other):\n"
    "        return self.x == other.x and self.y == other.y\n"
    "    pull __lt__(other):\n"
    "        return self.x * self.x + self.y * self.y < other.x * other.x + other.y * other.y\n"
    "    pull __neg__():\n"
    "        return Vec(-self.x, -self.y)\n"
    "    pull __str__():\n"
    '        return f"Vec({self.x}, {self.y})"\n'
)


def test_operator_overloading_arithmetic_and_str():
    out = run(VEC_CLASS + "print(Vec(1, 2) + Vec(3, 4))\nprint(Vec(1, 2) * 3)\nprint(-Vec(1, 2))\n")
    assert out == "Vec(4, 6)\nVec(3, 6)\nVec(-1, -2)\n"


def test_operator_overloading_eq_ne_and_lt():
    out = run(
        VEC_CLASS + "print(Vec(1, 2) == Vec(1, 2))\n"
        "print(Vec(1, 2) == Vec(9, 9))\n"
        "print(Vec(1, 2) != Vec(9, 9))\n"
        "print(Vec(1, 2) < Vec(3, 4))\n"
    )
    assert out == "true\nfalse\ntrue\ntrue\n"


def test_str_dunder_used_by_fstring_interpolation():
    out = run(VEC_CLASS + 'print(f"it is {Vec(1, 2)}")\n')
    assert out == "it is Vec(1, 2)\n"


def test_class_without_str_dunder_still_falls_back_to_repr():
    # No regression for the common case: a plain class with no __str__ should
    # print the same "<ClassName instance>" fallback as before this feature.
    out = run("class Plain:\n    pull init(n):\n        self.n = n\nprint(Plain(5))\n")
    assert out == "<Plain instance>\n"


def test_str_dunder_must_return_a_string():
    msg = run_expect_error(
        "class Bad:\n    pull __str__():\n        return 5\nprint(Bad())\n"
    )
    assert "__str__() must return a string" in msg


def test_comparison_dunder_result_is_normalized_to_a_real_boolean():
    # A sloppy __eq__ that returns a non-boolean (here, a number) should still
    # come out as true/false through == and !=, not leak the raw 5 through.
    out = run(
        "class Loose:\n    pull __eq__(other):\n        return 5\nprint(Loose() == Loose())\nprint(Loose() != Loose())\n"
    )
    assert out == "true\nfalse\n"


def test_destructuring_non_list_is_a_clear_error():
    msg = run_expect_error("let a, b = 5\n")
    assert "cannot unpack" in msg


def test_json_round_trip():
    out = run(
        'let data = {"name": "Ada", "tags": ["math", "engine"], "active": true, "id": nil}\n'
        "let text = json_encode(data)\n"
        "let back = json_decode(text)\n"
        'print(back["name"])\n'
        'print(back["tags"])\n'
        'print(back["active"])\n'
        'print(back["id"])\n'
    )
    assert out == "Ada\n[\"math\", \"engine\"]\ntrue\nnil\n"


def test_json_encode_pretty_flag_changes_formatting():
    compact = run('print(json_encode({"a": 1}))\n')
    pretty = run('print(json_encode({"a": 1}, true))\n')
    assert compact == '{"a": 1}\n'
    assert "\n" in pretty  # pretty-printed spans multiple lines


def test_json_decode_invalid_json_error():
    msg = run_expect_error('json_decode("{not valid json")\n')
    assert "invalid JSON" in msg


def test_json_encode_rejects_function():
    msg = run_expect_error("pull f(): return 1\njson_encode(f)\n")
    assert "json_encode" in msg


def test_sha256_is_deterministic_and_hex():
    out = run('print(sha256("hello"))\nprint(sha256("hello") == sha256("hello"))\nprint(sha256("hello") == sha256("world"))\n')
    lines = out.splitlines()
    assert len(lines[0]) == 64
    assert all(c in "0123456789abcdef" for c in lines[0])
    assert lines[1] == "true"
    assert lines[2] == "false"


def test_random_int_stays_in_range():
    out = run(
        "let ok = true\n"
        "let i = 0\n"
        "while i < 50:\n"
        "    let n = random_int(1, 6)\n"
        "    if n < 1 or n > 6:\n"
        "        ok = false\n"
        "    i += 1\n"
        "print(ok)\n"
    )
    assert out == "true\n"


def test_random_choice_and_shuffle_preserve_elements():
    out = run(
        "let xs = [1, 2, 3, 4, 5]\n"
        "print(has(xs, random_choice(xs)))\n"
        "let shuffled = shuffle(xs)\n"
        "print(sorted(shuffled) == sorted(xs))\n"
    )
    assert out == "true\ntrue\n"


def test_env_get_reads_and_defaults(monkeypatch):
    monkeypatch.setenv("QUILL_TEST_VAR", "hi there")
    out = run('print(env_get("QUILL_TEST_VAR"))\nprint(env_get("QUILL_NOPE", "fallback"))\n')
    assert out == "hi there\nfallback\n"
