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


def test_multiple_inheritance_independent_mixins():
    out = run(
        "class Mixin1:\n"
        "    pull hello():\n"
        '        return "hi"\n'
        "class Mixin2:\n"
        "    pull bye():\n"
        '        return "bye"\n'
        "class Combined(Mixin1, Mixin2):\n"
        "    pull init():\n"
        "        self.x = 1\n"
        "let c = Combined()\n"
        "print(c.hello())\n"
        "print(c.bye())\n"
        "print(type(c))\n"
    )
    assert out == "hi\nbye\nCombined\n"


def test_multiple_inheritance_diamond_cooperative_super():
    # D(B, C) where both B and C extend A. C3 linearization gives D's MRO as
    # [D, B, C, A] (same as Python's for this exact shape), so cooperative
    # super calls visit the shared ancestor A exactly once, in a consistent
    # order, regardless of which branch is walked first.
    out = run(
        "class A:\n"
        "    pull greet():\n"
        '        return "A"\n'
        "class B(A):\n"
        "    pull greet():\n"
        '        return "B->" + super.greet()\n'
        "class C(A):\n"
        "    pull greet():\n"
        '        return "C->" + super.greet()\n'
        "class D(B, C):\n"
        "    pull greet():\n"
        '        return "D->" + super.greet()\n'
        "print(D().greet())\n"
    )
    assert out == "D->B->C->A\n"


def test_multiple_inheritance_method_lookup_follows_base_order():
    # When two bases both define the same method and the subclass doesn't
    # override it, the first-listed base wins - matching Python's left-to-right
    # MRO precedence.
    out = run(
        "class A:\n"
        "    pull which():\n"
        '        return "A"\n'
        "class B:\n"
        "    pull which():\n"
        '        return "B"\n'
        "class First(A, B):\n"
        "    pull init(): self.x = 1\n"
        "class Second(B, A):\n"
        "    pull init(): self.x = 1\n"
        "print(First().which())\n"
        "print(Second().which())\n"
    )
    assert out == "A\nB\n"


def test_multiple_inheritance_duplicate_base_is_an_error():
    msg = run_expect_error(
        "class Base:\n"
        "    pull init(): self.x = 1\n"
        "class Bad(Base, Base):\n"
        "    pull noop(): return 0\n"
    )
    assert "more than once" in msg


def test_multiple_inheritance_inconsistent_mro_is_an_error():
    # Python's own classic example: X(A, B) and Y(B, A) disagree on the
    # relative order of A and B, so Z(X, Y) has no consistent linearization.
    msg = run_expect_error(
        "class A:\n"
        "    pull noop(): return 0\n"
        "class B:\n"
        "    pull noop(): return 0\n"
        "class X(A, B):\n"
        "    pull noop(): return 0\n"
        "class Y(B, A):\n"
        "    pull noop(): return 0\n"
        "class Z(X, Y):\n"
        "    pull noop(): return 0\n"
    )
    assert "consistent method resolution order" in msg


def test_super_with_no_ancestor_method_is_an_error():
    msg = run_expect_error(
        "class Bar:\n"
        "    pull noop():\n"
        "        return super.noop()\n"
        "Bar().noop()\n"
    )
    assert "has no ancestor with method" in msg


def test_class_empty_parens_means_no_bases():
    out = run("class Foo():\n    pull init():\n        self.x = 1\nprint(Foo().x)\n")
    assert out == "1\n"


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


def test_password_hash_round_trips_and_rejects_wrong_password():
    out = run(
        'let h = password_hash("hunter2")\n'
        'print(password_verify("hunter2", h))\n'
        'print(password_verify("wrong", h))\n'
    )
    assert out.splitlines() == ["true", "false"]


def test_password_hash_is_salted():
    out = run('print(password_hash("hunter2") == password_hash("hunter2"))\n')
    assert out.strip() == "false"


def test_password_verify_rejects_malformed_hash_instead_of_crashing():
    out = run('print(password_verify("hunter2", "not-a-real-hash"))\n')
    assert out.strip() == "false"


def test_all_and_any():
    out = run("print(all([1, 2, 3]))\nprint(all([1, 0, 3]))\nprint(any([0, 0, 3]))\nprint(any([0, 0]))\n")
    assert out.splitlines() == ["true", "false", "true", "false"]


def test_chr_and_ord_round_trip():
    out = run('print(chr(65))\nprint(ord("A"))\nprint(chr(ord("z")))\n')
    assert out.splitlines() == ["A", "65", "z"]


def test_hex_oct_bin():
    out = run("print(hex(255))\nprint(oct(8))\nprint(bin(5))\n")
    assert out.splitlines() == ["0xff", "0o10", "0b101"]


def test_pow_two_and_three_arg():
    out = run("print(pow(2, 10))\nprint(pow(2, 10, 1000))\n")
    assert out.splitlines() == ["1024", "24"]


def test_divmod_returns_pair():
    out = run("print(divmod(17, 5))\n")
    assert out.strip() == "[3, 2]"


def test_divmod_by_zero_is_clean_error():
    msg = run_expect_error("divmod(1, 0)\n")
    assert "divmod" in msg


def test_repr_quotes_strings_but_not_numbers():
    out = run('print(repr("hi"))\nprint(repr(5))\n')
    assert out.splitlines() == ['"hi"', "5"]


def test_math_functions():
    out = run("print(round(exp(1), 5))\nprint(round(sin(0), 5))\nprint(round(cos(0), 5))\nprint(gcd(12, 18))\n")
    assert out.splitlines() == ["2.71828", "0", "1", "6"]


def test_log_default_and_custom_base():
    out = run("print(round(log(E), 10))\nprint(log(8, 2))\n")
    assert out.splitlines() == ["1", "3"]


def test_top_level_map_filter_reduce():
    out = run(
        "print(map(pull(x): return x * 2, [1, 2, 3]))\n"
        "print(filter(pull(x): return x > 1, [1, 2, 3]))\n"
        "print(reduce(pull(acc, x): return acc + x, [1, 2, 3], 0))\n"
    )
    assert out.splitlines() == ["[2, 4, 6]", "[2, 3]", "6"]


def test_sorted_with_key_and_with_reverse():
    out = run(
        'let people = [{"name": "Bo", "age": 30}, {"name": "Al", "age": 20}]\n'
        'print(sorted(people, pull(p): return p["age"])[0]["name"])\n'
        "print(sorted([3, 1, 2], true))\n"
    )
    assert out.splitlines() == ["Al", "[3, 2, 1]"]


def test_min_max_with_key():
    out = run(
        'let people = [{"name": "Bo", "age": 30}, {"name": "Al", "age": 20}]\n'
        'print(min(people, pull(p): return p["age"])["name"])\n'
        'print(max(people, pull(p): return p["age"])["name"])\n'
    )
    assert out.splitlines() == ["Al", "Bo"]


def test_new_string_methods():
    out = run(
        'print("hello world".count("o"))\n'
        'print("5".pad_start(3, "0"))\n'
        'print("5".pad_end(3, "-"))\n'
        'print("hello".capitalize())\n'
        'print("Hello".swap_case())\n'
        'print("hello".reverse())\n'
        'print("  hi".trim_start())\n'
        'print("hi  ".trim_end())\n'
        'print("hello".index("l"))\n'
    )
    assert out.splitlines() == ["2", "005", "5--", "Hello", "hELLO", "olleh", "hi", "hi", "2"]


def test_string_predicate_methods():
    out = run(
        'print("123".is_digit())\n'
        'print("abc".is_alpha())\n'
        'print("abc123".is_alnum())\n'
        'print("ABC".is_upper())\n'
        'print("abc".is_lower())\n'
        'print("   ".is_space())\n'
    )
    assert out.splitlines() == ["true"] * 6


def test_string_index_raises_when_not_found():
    msg = run_expect_error('"hello".index("z")\n')
    assert "not found" in msg


def test_repeat_with_bad_argument_is_a_clean_error_not_a_traceback():
    msg = run_expect_error('"abc".repeat("x")\n')
    assert "repeat" in msg and "number" in msg


def test_new_list_methods():
    out = run(
        "let xs = [1, 2, 3]\n"
        "xs.insert(1, 99)\n"
        "print(xs)\n"
        "xs.remove(99)\n"
        "print(xs)\n"
        "print(xs.copy())\n"
        "let ys = [1, 2]\n"
        "ys.extend([3, 4])\n"
        "print(ys)\n"
        "print([1, 2, 2, 3].count(2))\n"
        "print([1, 2, 2, 3, 1].unique())\n"
        "print([[1, 2], [3], 4].flatten())\n"
        "let zs = [1, 2, 3]\n"
        "zs.clear()\n"
        "print(zs)\n"
    )
    assert out.splitlines() == [
        "[1, 99, 2, 3]",
        "[1, 2, 3]",
        "[1, 2, 3]",
        "[1, 2, 3, 4]",
        "2",
        "[1, 2, 3]",
        "[1, 2, 3, 4]",
        "[]",
    ]


def test_list_remove_missing_value_is_clean_error():
    msg = run_expect_error("[1, 2].remove(99)\n")
    assert "not found" in msg


def test_new_map_methods():
    out = run(
        '''let m = {"a": 1, "b": 2}
print(m.pop("a"))
print(m)
print(m.copy())
m.update({"c": 3})
print(m)
print(m.setdefault("d", 4))
print(m.setdefault("d", 99))
print(m)
'''
    )
    assert out.splitlines() == [
        "1",
        '{"b": 2}',
        '{"b": 2}',
        '{"b": 2, "c": 3}',
        "4",
        "4",
        '{"b": 2, "c": 3, "d": 4}',
    ]


def test_map_pop_missing_key_without_default_is_clean_error():
    msg = run_expect_error('{"a": 1}.pop("z")\n')
    assert "not found" in msg


def test_regex_match_find_and_find_all():
    out = run(
        'print(regex_match("[0-9]+", "abc123"))\n'
        'print(regex_match("^[0-9]+$", "abc123"))\n'
        'print(regex_find("[0-9]+", "abc123def456"))\n'
        'print(regex_find_all("[0-9]+", "abc123def456"))\n'
    )
    assert out.splitlines() == ["true", "false", "123", '["123", "456"]']


def test_regex_replace_and_split():
    out = run('print(regex_replace("[0-9]+", "abc123def456", "#"))\nprint(regex_split(",\\\\s*", "a, b,c"))\n')
    assert out.splitlines() == ["abc#def#", '["a", "b", "c"]']


def test_regex_groups_and_no_match():
    out = run('print(regex_groups("(\\\\w+)@(\\\\w+)", "bob@example"))\nprint(regex_groups("[0-9]+", "abc"))\n')
    assert out.splitlines() == ['["bob", "example"]', "nil"]


def test_regex_invalid_pattern_is_a_clean_error():
    msg = run_expect_error('regex_match("(", "x")\n')
    assert "invalid regex pattern" in msg


def test_time_and_sleep():
    out = run("let t = time()\nprint(type(t))\nsleep(0)\nprint(time() >= t)\n")
    assert out.splitlines() == ["number", "true"]


def test_uuid_is_unique_and_well_formed():
    out = run("let a = uuid()\nlet b = uuid()\nprint(a != b)\nprint(len(a))\n")
    assert out.splitlines() == ["true", "36"]


def test_base64_round_trip():
    out = run('print(base64_decode(base64_encode("hello, quill")))\n')
    assert out.strip() == "hello, quill"


def test_filesystem_helpers(tmp_path):
    target_dir = str(tmp_path / "sub").replace("\\", "\\\\")
    target_file = str(tmp_path / "sub" / "a.txt").replace("\\", "\\\\")
    out = run(
        f'make_dir("{target_dir}")\n'
        f'write_file("{target_file}", "hi")\n'
        f'print(file_exists("{target_file}"))\n'
        f'print(list_dir("{target_dir}"))\n'
        f'delete_file("{target_file}")\n'
        f'print(file_exists("{target_file}"))\n'
        "print(type(cwd()))\n"
    )
    assert out.splitlines() == ["true", '["a.txt"]', "false", "string"]


def test_path_join():
    out = run('print(path_join(["a", "b", "c.txt"]))\n')
    import os

    assert out.strip() == os.path.join("a", "b", "c.txt")


def test_more_math_functions():
    out = run(
        "print(log2(8))\n"
        "print(log10(1000))\n"
        "print(round(degrees(PI), 3))\n"
        "print(round(radians(180), 5))\n"
        "print(hypot(3, 4))\n"
        "print(factorial(5))\n"
    )
    assert out.splitlines() == ["3", "3", "180", "3.14159", "5", "120"]


def test_factorial_rejects_negative_and_non_integer():
    assert "factorial" in run_expect_error("factorial(-1)\n")
    assert "factorial" in run_expect_error("factorial(1.5)\n")


def test_more_string_methods():
    out = run(
        'print("hi".center(6, "*"))\n'
        'print("42".zfill(5))\n'
        'print("prefix_value".remove_prefix("prefix_"))\n'
        'print("value_suffix".remove_suffix("_suffix"))\n'
        'print("a\\nb\\nc".split_lines())\n'
    )
    assert out.splitlines() == ["**hi**", "00042", "value", "value", '["a", "b", "c"]']


def test_more_list_methods():
    out = run(
        "print([1, 2, 3, 4, 5].chunk(2))\n"
        "print([1, 2, 3, 4, 5, 6].group_by(pull(x): return x % 2))\n"
        "print([1, 2, 3].flat_map(pull(x): return [x, x * 10]))\n"
    )
    assert out.splitlines() == [
        "[[1, 2], [3, 4], [5]]",
        '{1: [1, 3, 5], 0: [2, 4, 6]}',
        "[1, 10, 2, 20, 3, 30]",
    ]


def test_assert_passes_silently_and_fails_with_message():
    out = run("assert(1 == 1)\nprint(\"ok\")\n")
    assert out.strip() == "ok"
    msg = run_expect_error('assert(1 == 2, "custom failure message")\n')
    assert msg == "custom failure message (line 1)"


def test_assert_default_message():
    msg = run_expect_error("assert(false)\n")
    assert "assertion failed" in msg


def test_exit_stops_execution_with_the_given_code():
    import contextlib
    import io

    from quill.builtins import build_globals
    from quill.interpreter import Interpreter
    from quill.lexer import tokenize
    from quill.parser import parse

    env = build_globals()
    interp = Interpreter(env)
    program = parse(tokenize('print("before")\nexit(7)\nprint("after")\n'))
    buf = io.StringIO()
    with pytest.raises(SystemExit) as exc_info:
        with contextlib.redirect_stdout(buf):
            interp.run(program)
    assert exc_info.value.code == 7
    assert buf.getvalue() == "before\n"


def test_deep_copy_is_independent_of_the_original():
    out = run(
        'let original = {"a": [1, 2, 3]}\n'
        "let copy = deep_copy(original)\n"
        'copy["a"].push(4)\n'
        'print(original["a"])\n'
        'print(copy["a"])\n'
    )
    assert out.splitlines() == ["[1, 2, 3]", "[1, 2, 3, 4]"]


def test_url_decode():
    out = run('print(url_decode("a%20b%2Bc"))\n')
    assert out.strip() == "a b+c"


def test_html_escape_and_unescape_round_trip():
    out = run(
        'print(html_escape("<b>1 & 2</b>"))\n'
        'print(html_unescape(html_escape("<b>1 & 2</b>")))\n'
    )
    assert out.splitlines() == ["&lt;b&gt;1 &amp; 2&lt;/b&gt;", "<b>1 & 2</b>"]


def test_csv_parse_and_stringify():
    out = run(
        'print(csv_parse("name,age\\nAda,36"))\n'
        'print(csv_stringify([["a", "b"], ["1", "2"]]))\n'
    )
    lines = out.splitlines()
    assert lines[0] == '[["name", "age"], ["Ada", "36"]]'
    assert lines[1] == "a,b"
    assert lines[2] == "1,2"


def test_bitwise_functions():
    out = run(
        "print(bit_and(12, 10))\n"
        "print(bit_or(12, 10))\n"
        "print(bit_xor(12, 10))\n"
        "print(bit_not(0))\n"
        "print(bit_shift_left(1, 4))\n"
        "print(bit_shift_right(16, 4))\n"
    )
    assert out.splitlines() == ["8", "14", "6", "-1", "16", "1"]


def test_bit_shift_rejects_negative_amount():
    assert "negative" in run_expect_error("bit_shift_left(1, -1)\n")


def test_type_predicates():
    out = run(
        "print(is_number(5))\n"
        'print(is_string("hi"))\n'
        "print(is_list([1]))\n"
        "print(is_map({}))\n"
        "print(is_bool(true))\n"
        "print(is_nil(nil))\n"
        "print(is_function(print))\n"
        "print(is_number(true))\n"
    )
    assert out.splitlines() == ["true"] * 7 + ["false"]


def test_is_class_distinguishes_class_from_instance():
    out = run("class Foo:\n    pull init(): self.x = 1\nprint(is_class(Foo))\nprint(is_class(Foo()))\n")
    assert out.splitlines() == ["true", "false"]


def test_inf_and_nan_constants():
    out = run("print(INF > 1000000)\nprint(NAN == NAN)\n")
    assert out.splitlines() == ["true", "false"]


def test_list_set_operations():
    out = run(
        "print([1, 2, 3].union([2, 3, 4]))\n"
        "print([1, 2, 3].intersect([2, 3, 4]))\n"
        "print([1, 2, 3].difference([2, 3, 4]))\n"
    )
    assert out.splitlines() == ["[1, 2, 3, 4]", "[2, 3]", "[1]"]


def test_default_parameter_values():
    out = run(
        'pull greet(name, greeting="Hello"):\n'
        '    return f"{greeting}, {name}!"\n'
        'print(greet("Ada"))\n'
        'print(greet("Ada", "Hi"))\n'
    )
    assert out.splitlines() == ["Hello, Ada!", "Hi, Ada!"]


def test_default_parameter_can_reference_an_earlier_parameter():
    out = run(
        "pull scale(x, factor=2, offset=x):\n"
        "    return x * factor + offset\n"
        "print(scale(5))\n"
        "print(scale(5, 3))\n"
        "print(scale(5, 3, 1))\n"
    )
    assert out.splitlines() == ["15", "20", "16"]


def test_default_parameters_on_anonymous_function_and_method():
    out = run(
        "let inc = pull(x, by=1): return x + by\n"
        "print(inc(10))\n"
        "print(inc(10, 5))\n"
        "class Counter:\n"
        "    pull init(start=0):\n"
        "        self.n = start\n"
        "    pull add(amount=1):\n"
        "        self.n = self.n + amount\n"
        "        return self.n\n"
        "let c = Counter()\n"
        "print(c.n)\n"
        "print(c.add())\n"
        "print(c.add(5))\n"
        "print(Counter(100).n)\n"
    )
    assert out.splitlines() == ["11", "15", "0", "1", "6", "100"]


def test_default_parameter_arity_error_shows_a_range():
    msg = run_expect_error('pull greet(name, greeting="Hello"):\n    return greeting\ngreet()\n')
    assert "expects 1-2 argument" in msg
    msg = run_expect_error('pull greet(name, greeting="Hello"):\n    return greeting\ngreet("a", "b", "c")\n')
    assert "expects 1-2 argument" in msg


def test_required_arity_message_unchanged_with_no_defaults():
    msg = run_expect_error("pull add(a, b):\n    return a + b\nadd(1)\n")
    assert "expects 2 argument" in msg


def test_non_default_parameter_after_default_is_a_parse_error():
    from quill.errors import ParseError
    from quill.lexer import tokenize
    from quill.parser import parse

    with pytest.raises(ParseError, match="without a default value follows"):
        parse(tokenize("pull f(a=1, b):\n    return a + b\n"))


def test_statistics_functions():
    out = run(
        "print(mean([1, 2, 3, 4]))\n"
        "print(median([1, 2, 3, 4]))\n"
        "print(mode([1, 1, 2, 3]))\n"
        "print(round(variance([2, 4, 4, 4, 5, 5, 7, 9]), 4))\n"
        "print(round(stdev([2, 4, 4, 4, 5, 5, 7, 9]), 4))\n"
        "print(percentile([1, 2, 3, 4, 5], 50))\n"
    )
    assert out.splitlines() == ["2.5", "2.5", "1", "4.5714", "2.1381", "3"]


def test_statistics_on_empty_list_is_a_clean_error():
    assert "empty" in run_expect_error("mean([])\n")


def test_date_format_and_parse():
    out = run('print(date_format(0, "%Y-%m-%d"))\nprint(type(date_parse("2024-01-15", "%Y-%m-%d")))\n')
    assert out.splitlines() == ["1970-01-01", "number"]


def test_clamp_lerp_sign():
    out = run(
        "print(clamp(15, 0, 10))\n"
        "print(clamp(-5, 0, 10))\n"
        "print(lerp(0, 10, 0.5))\n"
        "print(sign(-5))\n"
        "print(sign(0))\n"
        "print(sign(5))\n"
    )
    assert out.splitlines() == ["10", "0", "5", "-1", "0", "1"]


def test_is_even_and_is_odd():
    out = run("print(is_even(4))\nprint(is_odd(4))\n")
    assert out.splitlines() == ["true", "false"]


def test_hex_encode_decode_round_trip():
    out = run('print(hex_decode(hex_encode("quill")))\n')
    assert out.strip() == "quill"


def test_hash_functions():
    out = run('print(len(md5("hi")))\nprint(len(sha1("hi")))\nprint(len(sha512("hi")))\n')
    assert out.splitlines() == ["32", "40", "128"]


def test_hmac_sha256_is_keyed():
    out = run(
        'print(hmac_sha256("key", "message") == hmac_sha256("key", "message"))\n'
        'print(hmac_sha256("key", "message") != hmac_sha256("key2", "message"))\n'
    )
    assert out.splitlines() == ["true", "true"]


def test_args_receives_extra_cli_arguments():
    import contextlib
    import io

    from quill.builtins import build_globals
    from quill.interpreter import Interpreter
    from quill.lexer import tokenize
    from quill.parser import parse

    env = build_globals(["foo", "bar", "--flag=1"])
    interp = Interpreter(env)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp.run(parse(tokenize("print(args())\n")))
    assert buf.getvalue() == '["foo", "bar", "--flag=1"]\n'


def test_args_defaults_to_empty_list():
    out = run("print(args())\n")
    assert out.strip() == "[]"


def test_platform_returns_a_string():
    out = run("print(type(platform()))\n")
    assert out.strip() == "string"


def test_text_wrap():
    out = run(
        'let lines = text_wrap("the quick brown fox", 10)\n'
        "print(lines.every(pull(line): return len(line) <= 10))\n"
        'print(lines.join(" "))\n'
    )
    assert out.splitlines() == ["true", "the quick brown fox"]


def test_sample_returns_requested_count_from_the_list():
    out = run("let s = sample([1, 2, 3, 4, 5], 3)\nprint(len(s))\nfor x in s:\n    assert([1,2,3,4,5].contains(x))\nprint(\"ok\")\n")
    assert out.splitlines() == ["3", "ok"]


def test_string_case_conversions():
    out = run(
        'print("helloWorld".to_snake_case())\n'
        'print("hello_world".to_camel_case())\n'
        'print("HelloWorld".to_kebab_case())\n'
        'print("XMLHttpRequest".to_snake_case())\n'
    )
    assert out.splitlines() == ["hello_world", "helloWorld", "hello-world", "xml_http_request"]


def test_is_ascii_and_byte_length():
    # "héllo" here is a Python string escape resolved before Quill ever sees the
    # source - Quill's own lexer has no \u escape at all, so this must not be written
    # as \\u (a literal backslash-u, which Quill would just pass through as "u").
    out = run('print("hello".is_ascii())\nprint("hello".byte_length())\nprint("héllo".byte_length())\n')
    assert out.splitlines() == ["true", "5", "6"]


def test_take_drop_family():
    out = run(
        "let xs = [1, 2, 3, 4, 5]\n"
        "print(xs.take(2))\n"
        "print(xs.drop(2))\n"
        "print(xs.take_last(2))\n"
        "print(xs.drop_last(2))\n"
        "print(xs.take_while(pull(x): return x < 3))\n"
        "print(xs.drop_while(pull(x): return x < 3))\n"
    )
    assert out.splitlines() == ["[1, 2]", "[3, 4, 5]", "[4, 5]", "[1, 2, 3]", "[1, 2]", "[3, 4, 5]"]


def test_find_find_index_partition_tally():
    out = run(
        "print([1, 2, 3, 4].find(pull(x): return x > 2))\n"
        "print([1, 2, 3, 4].find_index(pull(x): return x > 2))\n"
        "print([1, 2, 3, 4].partition(pull(x): return x % 2 == 0))\n"
        "print([1, 1, 2, 3, 3, 3].tally())\n"
    )
    assert out.splitlines() == ["3", "2", "[[2, 4], [1, 3]]", "{1: 2, 2: 1, 3: 3}"]


def test_every_some_zip_with_rotate():
    out = run(
        "print([2, 4, 6].every(pull(x): return x % 2 == 0))\n"
        "print([2, 4, 5].some(pull(x): return x % 2 != 0))\n"
        "print([1, 2, 3].zip_with([10, 20, 30], pull(a, b): return a + b))\n"
        "print([1, 2, 3, 4, 5].rotate(2))\n"
    )
    assert out.splitlines() == ["true", "true", "[11, 22, 33]", "[3, 4, 5, 1, 2]"]


def test_list_shuffle_and_choice_methods():
    out = run("print(len([1, 2, 3].shuffle()))\nprint([1, 2, 3].contains([1, 2, 3].choice()))\n")
    assert out.splitlines() == ["3", "true"]


def test_map_utility_methods():
    out = run(
        '''let m = {"a": 1, "b": 2, "c": 3}
print(m.map_values(pull(v): return v * 10))
print(m.merged({"c": 99, "d": 4}))
print(m)
print({"a": 1, "b": 2}.invert())
print(m.pick(["a", "c"]))
print(m.omit(["a", "c"]))
print(m.key_of(2))
print(m.key_of(999))
'''
    )
    assert out.splitlines() == [
        '{"a": 10, "b": 20, "c": 30}',
        '{"a": 1, "b": 2, "c": 99, "d": 4}',
        '{"a": 1, "b": 2, "c": 3}',
        '{1: "a", 2: "b"}',
        '{"a": 1, "c": 3}',
        '{"b": 2}',
        "b",
        "nil",
    ]


def test_tau_constant():
    out = run("print(round(TAU / PI, 5))\n")
    assert out.strip() == "2"


def test_string_needle_methods_reject_non_string_arg_cleanly():
    # regression test: these used to crash with a raw, uncatchable Python
    # TypeError instead of a clean, catchable Quill error
    for expr in [
        '"hello".contains(5)',
        '"hello".starts_with(5)',
        '"hello".ends_with(5)',
        '"hello".find(5)',
        '"hello".index(5)',
        '"hello".count(5)',
        '"hello".replace(5, "x")',
        '"hello".replace("h", 5)',
        '"hello".remove_prefix(5)',
        '"hello".remove_suffix(5)',
        '"a,b".split(5)',
    ]:
        msg = run_expect_error(expr + "\n")
        assert "expects a string" in msg, f"{expr!r} -> {msg!r}"


def test_string_needle_methods_still_work_normally():
    out = run(
        'print("hello".contains("ell"))\n'
        'print("hello".starts_with("he"))\n'
        'print("hello".ends_with("lo"))\n'
        'print("hello".replace("l", "L"))\n'
        'print("a,b".split(","))\n'
    )
    assert out.splitlines() == ["true", "true", "true", "heLLo", '["a", "b"]']


def test_map_lookup_with_unhashable_key_is_a_clean_error_not_a_crash():
    # regression test: m[[1,2]], .has(), .get(), .pop(), .setdefault(), and the
    # top-level has() all used to crash with a raw Python TypeError
    for expr in [
        '{"a": 1}.has([1, 2])',
        '{"a": 1}.get([1, 2])',
        '{"a": 1}.pop([1, 2])',
        '{"a": 1}.setdefault([1, 2], "x")',
        'has({"a": 1}, [1, 2])',
        '{"a": 1}[[1, 2]]',
    ]:
        msg = run_expect_error(f"print({expr})\n")
        assert "map keys must be" in msg, f"{expr!r} -> {msg!r}"


def test_map_index_assignment_with_unhashable_key_is_a_clean_error():
    msg = run_expect_error('let m = {"a": 1}\nm[[1, 2]] = "x"\n')
    assert "map keys must be" in msg


def test_map_lookups_still_work_normally():
    out = run(
        '''let m = {"a": 1}
print(m.has("a"))
print(m.get("a"))
print(m["a"])
m["b"] = 2
print(m)
'''
    )
    assert out.splitlines() == ["true", "1", "1", '{"a": 1, "b": 2}']


def test_two_string_functions_report_which_argument_and_type_are_wrong():
    assert "string key" in run_expect_error('hmac_sha256(5, "msg")\n')
    assert "string password" in run_expect_error('password_verify(5, "x")\n')
    assert "string pattern" in run_expect_error('regex_match(5, "x")\n')


def test_list_remove_and_map_pop_error_wording():
    msg = run_expect_error("[1, 2, 3].remove(99)\n")
    assert msg == "value not found in list: 99 (line 1)"
    msg = run_expect_error('{"a": 1}.pop("z")\n')
    assert msg == "key not found: 'z' (line 1)"


def test_list_min_max_sum_methods():
    out = run(
        "print([3, 1, 2].min())\n"
        "print([3, 1, 2].max())\n"
        "print([1, 2, 3].sum())\n"
        'print([{"age": 30}, {"age": 20}].min(pull(p): return p["age"])["age"])\n'
    )
    assert out.splitlines() == ["1", "3", "6", "20"]


def test_list_first_and_last():
    out = run("print([1, 2, 3].first())\nprint([1, 2, 3].last())\n")
    assert out.splitlines() == ["1", "3"]
    assert "empty" in run_expect_error("[].first()\n")
    assert "empty" in run_expect_error("[].last()\n")


def test_list_last_index_of_repeat_flatten_deep_pairwise():
    out = run(
        "print([1, 2, 3, 2, 1].last_index_of(2))\n"
        "print([1, 2].repeat(3))\n"
        "print([[1, [2, 3]], [4]].flatten_deep())\n"
        "print([1, 2, 3, 4].pairwise())\n"
    )
    assert out.splitlines() == ["3", "[1, 2, 1, 2, 1, 2]", "[1, 2, 3, 4]", "[[1, 2], [2, 3], [3, 4]]"]


def test_string_equals_ignore_case():
    out = run('print("HELLO".equals_ignore_case("hello"))\nprint("HELLO".equals_ignore_case("world"))\n')
    assert out.splitlines() == ["true", "false"]


def test_filesystem_round_out(tmp_path):
    a = str(tmp_path / "a.txt").replace("\\", "\\\\")
    b = str(tmp_path / "b.txt").replace("\\", "\\\\")
    c = str(tmp_path / "c.txt").replace("\\", "\\\\")
    d = str(tmp_path / "sub").replace("\\", "\\\\")
    out = run(
        f'write_file("{a}", "hello")\n'
        f'copy_file("{a}", "{b}")\n'
        f'print(file_exists("{b}"))\n'
        f'print(file_size("{a}"))\n'
        f'move_file("{b}", "{c}")\n'
        f'print(file_exists("{b}"))\n'
        f'print(file_exists("{c}"))\n'
        f'make_dir("{d}")\n'
        f'delete_dir("{d}")\n'
        f'print(file_exists("{d}"))\n'
    )
    assert out.splitlines() == ["true", "5", "false", "true", "false"]


def test_env_all_returns_a_map():
    out = run("print(type(env_all()))\n")
    assert out.strip() == "map"


def test_levenshtein():
    out = run(
        'print(levenshtein("kitten", "sitting"))\n'
        'print(levenshtein("same", "same"))\n'
        'print(levenshtein("", "abc"))\n'
    )
    assert out.splitlines() == ["3", "0", "3"]


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
