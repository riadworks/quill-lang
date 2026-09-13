import io
import contextlib

from quill.cli import run_file


def test_missing_script_file_gives_clean_error_not_a_traceback():
    # Found via real use: running `quill site.ql` from the wrong directory
    # raised a raw Python FileNotFoundError traceback instead of the same
    # clean "Error: ..." format every other failure mode in this CLI uses.
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = run_file("this_file_does_not_exist.ql")
    assert code == 1
    assert "Error: cannot open" in err.getvalue()
    assert "Traceback" not in err.getvalue()
