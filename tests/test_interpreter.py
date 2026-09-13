from tests.helpers import run, run_expect_error


def test_hello_world_and_interpolation():
    out = run('let name = "world"\nprint("Hello, {name}!")\n')
    assert out == "Hello, world!\n"


def test_arithmetic_and_precedence():
    out = run("print(2 + 3 * 4)\nprint((2 + 3) * 4)\nprint(2 ** 10)\nprint(7 % 3)\n")
    assert out == "14\n20\n1024\n1\n"


def test_if_elif_else():
    out = run(
        "fn classify(n):\n"
        "    if n < 0:\n"
        '        return "neg"\n'
        "    elif n == 0:\n"
        '        return "zero"\n'
        "    else:\n"
        '        return "pos"\n'
        "print(classify(-5))\n"
        "print(classify(0))\n"
        "print(classify(5))\n"
    )
    assert out == "neg\nzero\npos\n"


def test_while_and_for_and_break_continue():
    out = run(
        "let i = 0\n"
        "while i < 10:\n"
        "    i = i + 1\n"
        "    if i % 2 == 0:\n"
        "        continue\n"
        "    if i > 7:\n"
        "        break\n"
        "    print(i)\n"
    )
    assert out == "1\n3\n5\n7\n"


def test_for_over_list_string_and_map():
    out = run('for c in "ab":\n    print(c)\nfor x in [1, 2]:\n    print(x)\n')
    assert out == "a\nb\n1\n2\n"


def test_recursion():
    out = run(
        "fn fact(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    return n * fact(n - 1)\n"
        "print(fact(6))\n"
    )
    assert out == "720\n"


def test_closures_are_independent_and_mutate_captured_scope():
    out = run(
        "fn make_counter():\n"
        "    let count = 0\n"
        "    fn increment():\n"
        "        count = count + 1\n"
        "        return count\n"
        "    return increment\n"
        "let a = make_counter()\n"
        "let b = make_counter()\n"
        "print(a())\nprint(a())\nprint(b())\n"
    )
    assert out == "1\n2\n1\n"


def test_lists_and_negative_indexing():
    out = run("let xs = [10, 20, 30]\nprint(xs[0])\nprint(xs[-1])\nxs[1] = 99\nprint(xs)\n")
    assert out == "10\n30\n[10, 99, 30]\n"


def test_maps():
    out = run('let m = {"a": 1, "b": 2}\nprint(m["a"])\nm["c"] = 3\nprint(len(m))\n')
    assert out == "1\n3\n"


def test_builtins_smoke():
    out = run(
        'print(len("hello"))\n'
        "print(type(5))\n"
        'print(type("x"))\n'
        "print(sorted([3, 1, 2]))\n"
        "print(sum([1, 2, 3]))\n"
        "print(abs(-5))\n"
        "print(round(3.7))\n"
    )
    assert out == "5\nnumber\nstring\n[1, 2, 3]\n6\n5\n4\n"


def test_and_or_short_circuit_and_truthiness():
    out = run(
        "fn noisy(v):\n"
        '    print("called")\n'
        "    return v\n"
        "let r = false and noisy(true)\n"
        "print(r)\n"
        "let r2 = true or noisy(false)\n"
        "print(r2)\n"
    )
    # noisy() must never be called because of short-circuiting
    assert out == "false\ntrue\n"


def test_truthiness_of_zero_and_empty():
    out = run(
        "if 0:\n"
        '    print("zero is truthy")\n'
        "else:\n"
        '    print("zero is falsy")\n'
        'if "":\n'
        '    print("empty str is truthy")\n'
        "else:\n"
        '    print("empty str is falsy")\n'
        "if [1]:\n"
        '    print("nonempty list is truthy")\n'
    )
    assert out == "zero is falsy\nempty str is falsy\nnonempty list is truthy\n"


def test_undefined_variable_error():
    msg = run_expect_error("print(nope)\n")
    assert "undefined variable" in msg
    assert "nope" in msg


def test_division_by_zero_error():
    msg = run_expect_error("let x = 1 / 0\n")
    assert "division by zero" in msg


def test_type_error_on_add():
    msg = run_expect_error('print(1 + "x")\n')
    assert "cannot add" in msg


def test_list_index_out_of_range_error():
    msg = run_expect_error("let xs = [1, 2]\nprint(xs[5])\n")
    assert "out of range" in msg


def test_wrong_arity_error():
    msg = run_expect_error("fn add(a, b):\n    return a + b\nprint(add(1))\n")
    assert "expects 2 argument" in msg


def test_assign_without_let_is_an_error():
    msg = run_expect_error("x = 5\n")
    assert "undefined variable" in msg


def test_nested_function_and_higher_order():
    out = run(
        "fn apply_twice(f, x):\n"
        "    return f(f(x))\n"
        "fn double(x):\n"
        "    return x * 2\n"
        "print(apply_twice(double, 3))\n"
    )
    assert out == "12\n"


def test_multiline_collection_literal_spans_lines():
    out = run("let xs = [\n    1,\n    2,\n    3,\n]\nprint(sum(xs))\n")
    assert out == "6\n"
