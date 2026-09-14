import json
import subprocess
import sys

from quill.lsp import compute_diagnostics


def test_compute_diagnostics_empty_for_valid_source():
    assert compute_diagnostics('print("hello")\n') == []


def test_compute_diagnostics_reports_line_and_message_for_invalid_source():
    diagnostics = compute_diagnostics("pull f(:\n    return 1\n")
    assert len(diagnostics) == 1
    assert diagnostics[0]["severity"] == 1
    assert diagnostics[0]["source"] == "quill"
    assert isinstance(diagnostics[0]["message"], str) and diagnostics[0]["message"]
    assert diagnostics[0]["range"]["start"]["line"] == 0  # 0-indexed for Quill's line 1


def _frame(message: dict) -> bytes:
    body = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        decoded = line.decode("ascii").strip()
        if decoded == "":
            break
        key, _, value = decoded.partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers["content-length"])
    return json.loads(stream.read(length).decode("utf-8"))


def test_lsp_server_over_real_stdio_protocol():
    # A genuine end-to-end check: spawn the actual `quill lsp` subprocess and
    # speak real Content-Length-framed JSON-RPC to it, the same way a real
    # editor's LSP client would - not just calling compute_diagnostics directly.
    proc = subprocess.Popen(
        [sys.executable, "-m", "quill.cli", "lsp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    try:
        proc.stdin.write(_frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
        proc.stdin.flush()
        init_resp = _read_message(proc.stdout)
        assert init_resp["id"] == 1
        assert init_resp["result"]["capabilities"]["textDocumentSync"] == 1

        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didOpen",
                    "params": {"textDocument": {"uri": "file:///bad.ql", "text": "pull f(:\n"}},
                }
            )
        )
        proc.stdin.flush()
        diag_msg = _read_message(proc.stdout)
        assert diag_msg["method"] == "textDocument/publishDiagnostics"
        assert len(diag_msg["params"]["diagnostics"]) == 1

        proc.stdin.write(
            _frame(
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didChange",
                    "params": {
                        "textDocument": {"uri": "file:///bad.ql"},
                        "contentChanges": [{"text": 'print("fixed")\n'}],
                    },
                }
            )
        )
        proc.stdin.flush()
        diag_msg2 = _read_message(proc.stdout)
        assert diag_msg2["params"]["diagnostics"] == []

        proc.stdin.write(_frame({"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None}))
        proc.stdin.flush()
        shutdown_resp = _read_message(proc.stdout)
        assert shutdown_resp["result"] is None

        proc.stdin.write(_frame({"jsonrpc": "2.0", "method": "exit", "params": None}))
        proc.stdin.flush()
        assert proc.wait(timeout=5) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
