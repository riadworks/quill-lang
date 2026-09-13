import "task.ql" as task_mod

let SAVE_FILE = "tasks.txt"
let PORT = 8080

# The admin key is "quill-admin" - only its sha256 hash is stored here, the
# same principle as a real password/API-key check: never keep the plaintext
# around, only compare hashes. See README.md for how this route is meant to
# be tried.
let ADMIN_KEY_HASH = "c9753125971ff0b3a78d128aad524b1817ee1e5b3c2aec7495742ba8e02c67fa"

pull load_tasks():
    let tasks = []
    if not file_exists(SAVE_FILE):
        return tasks
    let content = read_file(SAVE_FILE)
    for line in content.split("\n"):
        if line.trim() != "":
            tasks.push(task_mod.task_from_line(line))
    return tasks

pull save_tasks(tasks):
    let lines = []
    for t in tasks:
        lines.push(t.to_line())
    write_file(SAVE_FILE, lines.join("\n"))

pull escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

pull task_to_map(t):
    return {"title": t.title, "priority": t.priority, "done": t.done}

pull render_row(t, i):
    let done_class = " done" if t.done else ""
    let mark = "&#10003;" if t.done else "&nbsp;"
    let safe_title = escape_html(t.title)
    return f"
      <li class=\"row{done_class}\">
        <span class=\"check\">{mark}</span>
        <span class=\"title\">{safe_title}</span>
        <span class=\"pill\">p{t.priority}</span>
        <a class=\"btn\" href=\"/complete?i={i}\">done</a>
        <a class=\"btn danger\" href=\"/remove?i={i}\">remove</a>
      </li>"

pull render_page(tasks):
    let rows = ""
    if len(tasks) == 0:
        rows = "<li class=\"empty\">No tasks yet - add one below.</li>"
    else:
        let i = 0
        while i < len(tasks):
            rows += render_row(tasks[i], i)
            i += 1

    return f"<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>Quill Tasks</title>
<style>
  :root {{
    --bg: #0b0d10; --panel: #14171c; --border: #262b33;
    --text: #e7e9ec; --dim: #8b93a0; --accent: #4f8cff; --accent2: #8b5cf6;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; font-family: -apple-system, Segoe UI, sans-serif;
    background: radial-gradient(900px 500px at 15% -10%, rgba(79,140,255,.16), transparent 60%),
                radial-gradient(900px 600px at 100% 10%, rgba(139,92,246,.14), transparent 55%),
                var(--bg);
    color: var(--text); display: flex; justify-content: center; padding: 48px 20px;
  }}
  .card {{
    width: 100%; max-width: 560px; background: rgba(255,255,255,.03);
    border: 1px solid var(--border); border-radius: 18px; padding: 28px 30px;
    backdrop-filter: blur(16px);
  }}
  h1 {{ margin: 0 0 4px; font-size: 26px; font-weight: 800; }}
  p.sub {{ margin: 0 0 24px; color: var(--dim); font-size: 14px; }}
  ul {{ list-style: none; margin: 0 0 26px; padding: 0; display: flex; flex-direction: column; gap: 8px; }}
  li.row {{
    display: flex; align-items: center; gap: 10px; padding: 10px 12px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; font-size: 14px;
  }}
  li.row.done .title {{ text-decoration: line-through; color: var(--dim); }}
  li.empty {{ color: var(--dim); padding: 10px 2px; font-size: 14px; }}
  .check {{ width: 18px; text-align: center; color: #59d68c; }}
  .title {{ flex: 1; }}
  .pill {{
    font-family: monospace; font-size: 11px; color: var(--dim);
    border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px;
  }}
  .btn {{
    font-size: 12px; text-decoration: none; color: var(--text); padding: 6px 12px;
    border-radius: 999px; background: rgba(255,255,255,.06); border: 1px solid var(--border);
  }}
  .btn:hover {{ filter: brightness(1.3); }}
  .btn.danger {{ color: #f6948b; }}
  form {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  input {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 999px;
    padding: 10px 16px; color: var(--text); font-size: 14px;
  }}
  input[name=title] {{ flex: 1; min-width: 160px; }}
  input[name=priority] {{ width: 90px; }}
  button {{
    border: none; border-radius: 999px; padding: 10px 20px; font-weight: 700; cursor: pointer;
    background: linear-gradient(135deg, var(--accent), var(--accent2)); color: #fff;
  }}
</style>
</head>
<body>
  <div class=\"card\">
    <h1>Quill Tasks</h1>
    <p class=\"sub\">A website. Written in Quill. Being served by Quill.</p>
    <ul>{rows}
    </ul>
    <form method=\"post\" action=\"/add\">
      <input name=\"title\" placeholder=\"New task\" required>
      <input name=\"priority\" placeholder=\"p1-5\" required>
      <button type=\"submit\">Add</button>
    </form>
  </div>
</body>
</html>"

pull handle(req):
    let tasks = load_tasks()

    if req["path"] == "/" and req["method"] == "GET":
        return render_page(tasks)

    if req["path"] == "/add" and req["method"] == "POST":
        let title = req["form"]["title"].trim()
        let priority = num(req["form"]["priority"].trim())
        tasks.push(task_mod.Task(title, priority))
        save_tasks(tasks)
        return {"redirect": "/"}

    if req["path"] == "/complete" and req["method"] == "GET":
        let idx = num(req["query"]["i"])
        tasks[idx].complete()
        save_tasks(tasks)
        return {"redirect": "/"}

    if req["path"] == "/remove" and req["method"] == "GET":
        let idx = num(req["query"]["i"])
        tasks.pop(idx)
        save_tasks(tasks)
        return {"redirect": "/"}

    if req["path"] == "/api/tasks" and req["method"] == "GET":
        let out = []
        for t in tasks:
            out.push(task_to_map(t))
        return {"body": json_encode(out, true), "content_type": "application/json"}

    if req["path"] == "/api/wipe" and req["method"] == "POST":
        let key = req["form"].get("key")
        if key == nil or sha256(key) != ADMIN_KEY_HASH:
            return {"status": 401, "body": json_encode({"error": "bad key"}), "content_type": "application/json"}
        save_tasks([])
        return {"body": json_encode({"ok": true, "wiped": len(tasks)}), "content_type": "application/json"}

    return {"status": 404, "body": "Not found", "content_type": "text/plain"}

print(f"Serving on http://127.0.0.1:{PORT}")
serve(PORT, handle)
