"""A minimal HTTP server bridge: lets a Quill program handle real HTTP requests.

The socket/HTTP-protocol plumbing lives here in Python (via the standard
library's http.server), same pattern as read_file/write_file bridging to
Python's filesystem calls. The Quill-facing surface is just one builtin,
serve(port, handler), where handler is a Quill function: it receives one
request map and returns either a plain string (treated as a 200 HTML body)
or a response map with optional status/body/content_type/redirect keys.
"""

import http.server
import urllib.parse


def _request_to_map(handler: http.server.BaseHTTPRequestHandler) -> dict:
    parsed = urllib.parse.urlparse(handler.path)
    query = dict(urllib.parse.parse_qsl(parsed.query))

    body = ""
    form = {}
    length = int(handler.headers.get("Content-Length", 0) or 0)
    if length:
        raw = handler.rfile.read(length).decode("utf-8", errors="replace")
        body = raw
        content_type = handler.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" in content_type:
            form = dict(urllib.parse.parse_qsl(raw))

    return {
        "method": handler.command,
        "path": parsed.path,
        "query": query,
        "form": form,
        "body": body,
    }


def _make_handler_class(quill_fn, call_fn):
    class QuillHTTPHandler(http.server.BaseHTTPRequestHandler):
        def _handle(self):
            req = _request_to_map(self)
            try:
                result = call_fn(quill_fn, [req], None)
            except Exception as exc:  # a bug in the Quill handler shouldn't kill the server
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Internal error: {exc}".encode("utf-8"))
                return

            redirect = None
            if isinstance(result, str):
                status, body, content_type = 200, result, "text/html; charset=utf-8"
            elif isinstance(result, dict):
                redirect = result.get("redirect")
                status = int(result.get("status", 302 if redirect else 200))
                body = result.get("body", "")
                content_type = result.get("content_type", "text/html; charset=utf-8")
            else:
                status, body, content_type = 200, str(result), "text/plain; charset=utf-8"

            self.send_response(status)
            if redirect:
                self.send_header("Location", redirect)
            self.send_header("Content-Type", content_type)
            body_bytes = body.encode("utf-8")
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            if body_bytes:
                self.wfile.write(body_bytes)

        def do_GET(self):
            self._handle()

        def do_POST(self):
            self._handle()

        def log_message(self, fmt, *args):
            pass  # keep the Quill program's own stdout clean

    return QuillHTTPHandler


def serve(port: int, quill_fn, call_fn) -> None:
    handler_class = _make_handler_class(quill_fn, call_fn)
    server = http.server.HTTPServer(("127.0.0.1", port), handler_class)
    server.serve_forever()
