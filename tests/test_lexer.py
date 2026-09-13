from quill.lexer import tokenize
from quill.tokens import T


def types(source):
    return [t.type for t in tokenize(source)]


def test_indent_dedent_basic():
    src = "if true:\n    print(1)\nprint(2)\n"
    t = types(src)
    assert t == [
        T.IF, T.TRUE, T.COLON, T.NEWLINE,
        T.INDENT, T.NAME, T.LPAREN, T.NUMBER, T.RPAREN, T.NEWLINE,
        T.DEDENT, T.NAME, T.LPAREN, T.NUMBER, T.RPAREN, T.NEWLINE,
        T.EOF,
    ]


def test_nested_indent_dedent():
    src = "if true:\n    if true:\n        print(1)\n    print(2)\nprint(3)\n"
    t = types(src)
    # two INDENTs going in, two DEDENTs coming back down to top level
    assert t.count(T.INDENT) == 2
    assert t.count(T.DEDENT) == 2


def test_blank_lines_and_comments_do_not_affect_indentation():
    src = "if true:\n    print(1)\n\n    # a comment\n    print(2)\nprint(3)\n"
    t = types(src)
    assert t.count(T.INDENT) == 1
    assert t.count(T.DEDENT) == 1


def test_newlines_suppressed_inside_brackets():
    src = "let xs = [\n    1,\n    2,\n]\n"
    t = types(src)
    # only one NEWLINE (after the closing bracket's line), none inside the list
    assert t.count(T.NEWLINE) == 1


def test_fstring_interpolation_tokenizes_as_single_string_token():
    tokens = tokenize('f"hello {name}"\n')
    assert tokens[0].type == T.STRING
    parts = tokens[0].value
    assert parts[0] == ("lit", "hello ")
    assert parts[1] == ("expr", "name")


def test_plain_string_does_not_split_out_interpolation():
    tokens = tokenize('"hello {name}"\n')
    assert tokens[0].type == T.STRING
    assert tokens[0].value == [("lit", "hello {name}")]


def test_inconsistent_indentation_raises():
    from quill.errors import LexError

    src = "if true:\n    print(1)\n  print(2)\n"
    try:
        tokenize(src)
        assert False, "expected a LexError"
    except LexError:
        pass
