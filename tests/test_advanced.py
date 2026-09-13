from tests.helpers import run, run_expect_error


def test_class_basic_fields_and_methods():
    out = run(
        "class Point:\n"
        "    fn init(x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "    fn to_string():\n"
        '        return "({self.x}, {self.y})"\n'
        "let p = Point(1, 2)\n"
        "print(p.x)\n"
        "print(p.to_string())\n"
    )
    assert out == "1\n(1, 2)\n"


def test_class_inheritance_and_super():
    out = run(
        "class Animal:\n"
        "    fn init(name):\n"
        "        self.name = name\n"
        "    fn speak():\n"
        '        return "{self.name} makes a sound"\n'
        "class Dog(Animal):\n"
        "    fn init(name, breed):\n"
        "        super.init(name)\n"
        "        self.breed = breed\n"
        "    fn speak():\n"
        '        return "{self.name} the {self.breed} barks"\n'
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
        "    fn tag():\n"
        '        return "A"\n'
        "class B(A):\n"
        "    fn tag():\n"
        '        return super.tag() + "B"\n'
        "class C(B):\n"
        "    fn tag():\n"
        '        return super.tag() + "C"\n'
        "print(C().tag())\n"
    )
    assert out == "ABC\n"


def test_class_wrong_init_arity_error():
    msg = run_expect_error(
        "class Point:\n"
        "    fn init(x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "Point(1)\n"
    )
    assert "expects 2 argument" in msg


def test_class_unknown_field_error():
    msg = run_expect_error(
        "class Point:\n"
        "    fn init(x):\n"
        "        self.x = x\n"
        "let p = Point(1)\n"
        "print(p.y)\n"
    )
    assert "has no field or method" in msg


def test_try_except_catches_raise():
    out = run('try:\n    raise "boom"\nexcept e:\n    print("caught {e}")\n')
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
        "fn f():\n"
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
        "print(xs.map(fn(x): return x + 1))\n"
        "print(xs.filter(fn(x): return x > 1))\n"
        "print(xs.reduce(fn(a, b): return a + b, 0))\n"
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
        "fn double(x):\n"
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

    (tmp_path / "mod.ql").write_text('let GREETING = "hi"\nfn shout(s):\n    return s.upper()\n', encoding="utf-8")
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
