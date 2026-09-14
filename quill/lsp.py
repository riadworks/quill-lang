"""A minimal Language Server Protocol server for Quill.

Provides exactly one thing: live syntax-error diagnostics - from the same
lexer/parser every `quill script.ql` run already goes through - as you type,
for any editor whose LSP client can be pointed at a command to run. There's
no completion, hover, or go-to-definition here, just "does this file parse,
and if not, where."

Wire an editor's generic LSP client at the command `quill lsp` (stdio
transport, no arguments) for files with a `.ql` extension - most editors'
LSP clients (Neovim's built-in client, Sublime's LSP package, Emacs's
eglot, VS Code's "Generic LSP Client" extensions) just need a command and a
language ID/file glob, not anything Quill-specific beyond that.
"""

import json
import sys

from quill.errors import QuillError
from quill.lexer import tokenize
from quill.parser import parse

_documents: dict = {}


def compute_diagnostics(text: str) -> list:
    """The one real piece of logic here - everything else is protocol
    plumbing. Returns an empty list for a file that parses cleanly, or one
    LSP Diagnostic pointing at the first Lex/ParseError otherwise."""
    try:
        parse(tokenize(text))
    except QuillError as exc:
        line = max((exc.line or 1) - 1, 0)  # LSP lines are 0-indexed, Quill's are 1-indexed
        return [
            {
                "range": {
                    "start": {"line": line, "character": 0},
                    "end": {"line": line, "character": 9999},
                },
                "severity": 1,  # Error
                "source": "quill",
                "message": exc.message,
            }
        ]
    return []


def _read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None  # EOF - the client closed the pipe
        decoded = line.decode("ascii", errors="replace").strip()
        if decoded == "":
            break
        if ":" in decoded:
            key, _, value = decoded.partition(":")
            headers[key.strip().lower()] = value.strip()
    try:
        length = int(headers.get("content-length", 0))
    except ValueError:
        length = 0
    if length <= 0:
        return {}
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(stream, message: dict) -> None:
    body = json.dumps(message).encode("utf-8")
    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    stream.write(body)
    stream.flush()


def _notify(stream, method: str, params: dict) -> None:
    _write_message(stream, {"jsonrpc": "2.0", "method": method, "params": params})


def _respond(stream, msg_id, result) -> None:
    _write_message(stream, {"jsonrpc": "2.0", "id": msg_id, "result": result})


def _publish(stream, uri: str, text: str) -> None:
    _notify(stream, "textDocument/publishDiagnostics", {"uri": uri, "diagnostics": compute_diagnostics(text)})


def run_server(stdin=None, stdout=None) -> int:
    stdin = stdin if stdin is not None else sys.stdin.buffer
    stdout = stdout if stdout is not None else sys.stdout.buffer

    while True:
        try:
            message = _read_message(stdin)
        except (ValueError, OSError):
            return 1
        if message is None:
            return 0

        method = message.get("method")
        msg_id = message.get("id")

        if method == "initialize":
            _respond(
                stdout,
                msg_id,
                {
                    "capabilities": {"textDocumentSync": 1},  # 1 = full document sync
                    "serverInfo": {"name": "quill-lsp", "version": "0.1.0"},
                },
            )
        elif method == "initialized":
            pass
        elif method == "textDocument/didOpen":
            doc = message["params"]["textDocument"]
            _documents[doc["uri"]] = doc["text"]
            _publish(stdout, doc["uri"], doc["text"])
        elif method == "textDocument/didChange":
            params = message["params"]
            uri = params["textDocument"]["uri"]
            changes = params.get("contentChanges", [])
            if changes:
                text = changes[-1].get("text", "")
                _documents[uri] = text
                _publish(stdout, uri, text)
        elif method == "textDocument/didClose":
            uri = message["params"]["textDocument"]["uri"]
            _documents.pop(uri, None)
            _notify(stdout, "textDocument/publishDiagnostics", {"uri": uri, "diagnostics": []})
        elif method == "shutdown":
            _respond(stdout, msg_id, None)
        elif method == "exit":
            return 0
        elif msg_id is not None:
            # An unrecognized request still gets a response, so the client
            # never hangs waiting on a method this minimal server doesn't implement.
            _respond(stdout, msg_id, None)
        # unrecognized notifications are simply ignored


if __name__ == "__main__":
    sys.exit(run_server())
