from quill.errors import QuillError
from quill.formatter import format_source


def test_normalizes_inconsistent_indentation_to_four_spaces():
    source = (
        "class Animal:\n"
        "  pull init(name):\n"
        "      self.name = name\n"
        "  pull speak():\n"
        '        return f"{self.name} makes a sound"\n'
    )
    expected = (
        "class Animal:\n"
        "    pull init(name):\n"
        "        self.name = name\n"
        "    pull speak():\n"
        '        return f"{self.name} makes a sound"\n'
    )
    assert format_source(source) == expected


def test_leaves_comments_and_blank_lines_untouched():
    source = "pull f():\n" "      # a comment, oddly indented\n" "\n" "        return 1\n"
    formatted = format_source(source)
    assert "# a comment, oddly indented" in formatted
    # the comment's own line is untouched even though the code around it was fixed
    assert "      # a comment, oddly indented\n" in formatted
    assert "    return 1\n" in formatted


def test_is_idempotent():
    source = "pull f(x):\n" "   if x:\n" "         return 1\n" "   return 2\n"
    once = format_source(source)
    twice = format_source(once)
    assert once == twice


def test_already_formatted_source_is_unchanged():
    source = "pull add(a, b):\n    return a + b\n\nprint(add(1, 2))\n"
    assert format_source(source) == source


def test_does_not_alter_program_behavior(tmp_path):
    from quill.builtins import build_globals
    from quill.interpreter import Interpreter
    from quill.lexer import tokenize
    from quill.parser import parse
    import contextlib
    import io

    def run(src):
        env = build_globals()
        interp = Interpreter(env)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            interp.run(parse(tokenize(src)))
        return buf.getvalue()

    messy = 'pull greet(name):\n   if name == "":\n           return "who?"\n   return f"hi {name}"\n\nprint(greet("Ada"))\n'
    formatted = format_source(messy)
    assert run(messy) == run(formatted) == "hi Ada\n"


def test_raises_a_quill_error_on_unparseable_source_rather_than_guessing():
    import pytest

    with pytest.raises(QuillError):
        format_source('print("unterminated\n')
