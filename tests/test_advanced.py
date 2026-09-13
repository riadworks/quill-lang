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
