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
<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
<link href=\"https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap\" rel=\"stylesheet\">
<style>
  :root {{
    --ink-900: #14161d; --ink-800: #1c1f28; --ink-600: #343947;
    --paper: #eef1ee; --brass: #c39a5c; --brass-bright: #ddb877; --oxblood: #b1555b;
    --text: #e8eae6; --dim: #9aa0a6; --rule: rgba(238, 241, 238, 0.09);
    --display: \"Fraunces\", Georgia, serif;
    --body: \"IBM Plex Sans\", -apple-system, \"Segoe UI\", sans-serif;
    --mono: \"IBM Plex Mono\", Consolas, monospace;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; font-family: var(--body);
    background: var(--ink-900); color: var(--text);
    display: flex; justify-content: center; padding: 56px 20px;
  }}
  .sheet {{
    width: 100%; max-width: 560px; background: var(--ink-800);
    border: 1px solid var(--ink-600); border-radius: 4px; padding: 34px 36px;
  }}
  .eyebrow {{
    font-family: var(--mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--brass-bright); margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
  }}
  .eyebrow::before {{ content: \"\"; width: 14px; height: 1px; background: var(--brass-bright); }}
  h1 {{ font-family: var(--display); margin: 0 0 4px; font-size: 27px; font-weight: 600; }}
  p.sub {{ margin: 0 0 26px; color: var(--dim); font-size: 14px; }}
  ul {{ list-style: none; margin: 0 0 28px; padding: 0; display: flex; flex-direction: column; }}
  li.row {{
    display: flex; align-items: center; gap: 10px; padding: 12px 2px;
    border-bottom: 1px solid var(--rule); font-size: 14px;
  }}
  li.row.done .title {{ text-decoration: line-through; color: var(--dim); }}
  li.empty {{ color: var(--dim); padding: 10px 2px; font-size: 14px; }}
  .check {{ width: 16px; text-align: center; color: var(--brass-bright); font-family: var(--mono); }}
  .title {{ flex: 1; }}
  .pill {{
    font-family: var(--mono); font-size: 11px; color: var(--dim);
    border: 1px solid var(--ink-600); border-radius: 3px; padding: 2px 7px;
  }}
  .btn {{
    font-family: var(--mono); font-size: 11.5px; text-decoration: none; color: var(--text);
    padding: 5px 10px; border: 1px solid var(--ink-600); border-radius: 3px;
  }}
  .btn:hover {{ border-color: var(--brass); color: var(--brass-bright); }}
  .btn.danger:hover {{ border-color: var(--oxblood); color: var(--oxblood); }}
  form {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  input {{
    background: var(--ink-900); border: 1px solid var(--ink-600); border-radius: 3px;
    padding: 10px 14px; color: var(--text); font-family: var(--body); font-size: 14px;
  }}
  input:focus {{ outline: none; border-color: var(--brass); }}
  input[name=title] {{ flex: 1; min-width: 160px; }}
  input[name=priority] {{ width: 90px; }}
  button {{
    font-family: var(--body); border: 1px solid var(--brass); border-radius: 3px; padding: 10px 20px;
    font-weight: 600; cursor: pointer; background: var(--brass); color: var(--ink-900);
  }}
  button:hover {{ background: var(--brass-bright); border-color: var(--brass-bright); }}
</style>
</head>
<body>
  <div class=\"sheet\">
    <p class=\"eyebrow\">Quill / tasks</p>
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
