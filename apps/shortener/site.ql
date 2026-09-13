import "store.ql" as store_mod

let SAVE_FILE = "links.txt"
let PORT = 8081

pull escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

pull render_row(code, url):
    let safe_url = escape_html(url)
    return f"
      <li class=\"row\">
        <a class=\"code\" href=\"/{code}\">/{code}</a>
        <span class=\"arrow\">&rarr;</span>
        <span class=\"url\">{safe_url}</span>
      </li>"

pull render_page(links):
    let codes = keys(links)
    let rows = ""
    if len(codes) == 0:
        rows = "<li class=\"empty\">No links yet - shorten one below.</li>"
    else:
        for code in codes:
            rows += render_row(code, links[code])

    return f"<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>Quill Shortener</title>
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
    width: 100%; max-width: 620px; background: rgba(255,255,255,.03);
    border: 1px solid var(--border); border-radius: 18px; padding: 28px 30px;
    backdrop-filter: blur(16px);
  }}
  h1 {{ margin: 0 0 4px; font-size: 26px; font-weight: 800; }}
  p.sub {{ margin: 0 0 24px; color: var(--dim); font-size: 14px; }}
  ul {{ list-style: none; margin: 0 0 26px; padding: 0; display: flex; flex-direction: column; gap: 8px; }}
  li.row {{
    display: flex; align-items: center; gap: 10px; padding: 10px 12px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px; font-size: 14px;
    overflow: hidden;
  }}
  li.empty {{ color: var(--dim); padding: 10px 2px; font-size: 14px; }}
  .code {{ font-family: monospace; color: var(--accent); text-decoration: none; flex-shrink: 0; }}
  .code:hover {{ text-decoration: underline; }}
  .arrow {{ color: var(--dim); flex-shrink: 0; }}
  .url {{ color: var(--dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  form {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  input {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 999px;
    padding: 10px 16px; color: var(--text); font-size: 14px; flex: 1; min-width: 200px;
  }}
  button {{
    border: none; border-radius: 999px; padding: 10px 20px; font-weight: 700; cursor: pointer;
    background: linear-gradient(135deg, var(--accent), var(--accent2)); color: #fff;
  }}
</style>
</head>
<body>
  <div class=\"card\">
    <h1>Quill Shortener</h1>
    <p class=\"sub\">A URL shortener. Written in Quill. Served by Quill.</p>
    <ul>{rows}
    </ul>
    <form method=\"post\" action=\"/shorten\">
      <input name=\"url\" placeholder=\"https://example.com/some/long/path\" required>
      <button type=\"submit\">Shorten</button>
    </form>
  </div>
</body>
</html>"

pull handle(req):
    let links = store_mod.load_links(SAVE_FILE)
    let path = req["path"]
    let method = req["method"]

    if path == "/" and method == "GET":
        return render_page(links)

    if path == "/shorten" and method == "POST":
        let url = req["form"].get("url")
        if url == nil or url.trim() == "":
            return {"status": 400, "body": "Missing url field", "content_type": "text/plain"}
        let code = store_mod.make_code(links)
        links[code] = url.trim()
        store_mod.save_links(SAVE_FILE, links)
        return {"redirect": "/"}

    if path == "/api/links" and method == "GET":
        return {"body": json_encode(links, true), "content_type": "application/json"}

    if method == "GET" and len(path) > 1:
        let code = slice(path, 1, len(path))
        if has(links, code):
            return {"redirect": links[code]}
        return {"status": 404, "body": f"No link for /{code}", "content_type": "text/plain"}

    return {"status": 404, "body": "Not found", "content_type": "text/plain"}

print(f"Serving on http://127.0.0.1:{PORT}")
serve(PORT, handle)
