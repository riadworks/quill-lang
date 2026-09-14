"""A minimal HTTP server bridge: lets a Quill program handle real HTTP requests.

The socket/HTTP-protocol plumbing lives here in Python (via the standard
library's http.server), same pattern as read_file/write_file bridging to
Python's filesystem calls. The Quill-facing surface is just one builtin,
serve(port, handler), where handler is a Quill function: it receives one
request map (with a "cookies" map parsed from the Cookie header) and returns
either a plain string (treated as a 200 HTML body) or a response map with
optional status/body/content_type/redirect/set_cookie keys.
"""

import http.server
import sys
import urllib.parse

# Keeps a client that lies about (or inflates) Content-Length from making the
# server try to buffer an unbounded body in memory.
MAX_BODY_BYTES = 10 * 1024 * 1024


def _parse_cookies(header_value: str) -> dict:
    cookies = {}
    for part in header_value.split(";"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[name.strip()] = urllib.parse.unquote(value.strip())
    return cookies


def _request_to_map(handler: http.server.BaseHTTPRequestHandler):
    """Returns (request_map, None) normally, or (None, (status, message)) if
    the request should be rejected before a Quill handler ever sees it."""
    parsed = urllib.parse.urlparse(handler.path)
    query = dict(urllib.parse.parse_qsl(parsed.query))
    cookies = _parse_cookies(handler.headers.get("Cookie", ""))

    try:
        length = int(handler.headers.get("Content-Length", 0) or 0)
    except ValueError:
        return None, (400, "invalid Content-Length header")
    if length < 0:
        return None, (400, "invalid Content-Length header")
    if length > MAX_BODY_BYTES:
        return None, (413, "request body too large")

    body = ""
    form = {}
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
        "cookies": cookies,
    }, None


def _make_handler_class(quill_fn, call_fn):
    class QuillHTTPHandler(http.server.BaseHTTPRequestHandler):
        def _handle(self):
            req, rejection = _request_to_map(self)
            if rejection is not None:
                status, message = rejection
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(message.encode("utf-8"))
                return

            try:
                result = call_fn(quill_fn, [req], None)
            except Exception as exc:
                # A bug in the Quill handler shouldn't kill the server - and it
                # shouldn't hand the visitor a raw exception message either, since
                # that can leak file paths or other internals to anyone who
                # manages to trigger an error. The real detail goes to the
                # server's own stderr, same place a CLI script's errors go.
                print(f"[quill server] unhandled error in handler: {exc}", file=sys.stderr)
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Internal Server Error")
                return

            redirect = None
            set_cookie = None
            if isinstance(result, str):
                status, body, content_type = 200, result, "text/html; charset=utf-8"
            elif isinstance(result, dict):
                redirect = result.get("redirect")
                set_cookie = result.get("set_cookie")
                status = int(result.get("status", 302 if redirect else 200))
                body = result.get("body", "")
                content_type = result.get("content_type", "text/html; charset=utf-8")
            else:
                status, body, content_type = 200, str(result), "text/plain; charset=utf-8"

            self.send_response(status)
            if redirect:
                self.send_header("Location", redirect)
            if isinstance(set_cookie, dict):
                for name, value in set_cookie.items():
                    encoded = urllib.parse.quote(str(value))
                    # HttpOnly keeps client-side script from reading the cookie (blunts
                    # XSS-driven session theft); SameSite=Lax blunts basic CSRF. No
                    # Secure flag - this server is HTTP-only, and Secure would silently
                    # stop the cookie from ever being sent.
                    self.send_header(
                        "Set-Cookie", f"{name}={encoded}; Path=/; HttpOnly; SameSite=Lax"
                    )
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

    return QuillHTTPHandler


def serve(port: int, quill_fn, call_fn) -> None:
    handler_class = _make_handler_class(quill_fn, call_fn)
    server = http.server.HTTPServer(("127.0.0.1", port), handler_class)
    server.serve_forever()
