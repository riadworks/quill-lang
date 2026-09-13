# Quill Tasks (web)

The same task manager as `apps/tasks/`, but as an actual website instead of a
terminal app — a small persistent to-do list you open in a browser, add
tasks to with a form, and mark done/remove with a click.

```powershell
cd apps\website
quill site.ql
```

Then open `http://127.0.0.1:8080/` in a browser. Tasks persist to
`tasks.txt` next to the script.

## What made this possible

Quill had no networking at all before this. Added a `serve(port, handler)`
builtin: the actual socket/HTTP-protocol handling lives in Python
(`quill/webserver.py`, built on the standard library's `http.server`), and
`handler` is a plain Quill function that receives one request map
(`method`, `path`, `query`, `form`, `body`) and returns either a string
(a 200 HTML body) or a response map (`status`, `body`, `content_type`,
`redirect`). Same bridging pattern as `read_file`/`write_file` — Python
handles the OS-level plumbing, Quill code handles the actual logic.

## A real bug this found in the language

`site.ql`'s HTML template embeds a `<style>` block, and CSS is full of
`{ }`. Since Quill's `f"..."` strings interpolate `{expr}`, every curly
brace in that CSS was being misread as the start of an interpolation —
the language had no way to write a *literal* brace inside an f-string at
all. Fixed by adding real escaping, `{{` → `{` and `}}` → `}` (the same
convention Python's own f-strings use), plus making a lone unmatched `}`
a clear error instead of silently doing something wrong. Verified by
loading the actual rendered page over real HTTP and confirming the CSS
came out with normal single braces, not doubled ones.

While testing that fix, the test suite itself turned out to have a gap
too: `run_expect_error()`, the test helper used everywhere to check that
bad code produces a clean error, only wrapped *execution* in a
try/except — an error raised while lexing or parsing (like this
brace-escaping bug's edge case) skipped past it entirely, uncaught. Fixed
the helper to wrap all three stages.

## Backend and security: two more routes

Two routes exist purely to demonstrate that Quill can do this properly, not
just serve HTML:

- **`GET /api/tasks`** — the same task list as JSON, via the new
  `json_encode()`/`json_decode()` builtins (they map directly onto Quill's
  own list/map/string/number/bool/nil runtime values, so most values need no
  conversion at all — only class instances do, hence `task_to_map()`).
  Try it: `curl http://127.0.0.1:8080/api/tasks`
- **`POST /api/wipe`** — clears every task, but only with the right key.
  The key is `"quill-admin"`; the script only ever stores its `sha256()`
  hash and compares hashes, never the plaintext — the same principle real
  password/API-key checks use. Try it:
  ```powershell
  Invoke-WebRequest http://127.0.0.1:8080/api/wipe -Method Post -Body "key=quill-admin" -ContentType "application/x-www-form-urlencoded"
  ```
  A wrong key gets a `401`, not a crash.

Both were verified against a live running server with real HTTP requests
(including the wrong-key case) before being considered done, same as
every other route in this app.
