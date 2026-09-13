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
    width: 100%; max-width: 620px; background: var(--ink-800);
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
    border-bottom: 1px solid var(--rule); font-size: 14px; overflow: hidden;
  }}
  li.empty {{ color: var(--dim); padding: 10px 2px; font-size: 14px; }}
  .code {{ font-family: var(--mono); color: var(--brass-bright); text-decoration: none; flex-shrink: 0; }}
  .code:hover {{ text-decoration: underline; }}
  .arrow {{ color: var(--dim); flex-shrink: 0; }}
  .url {{ color: var(--dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  form {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  input {{
    background: var(--ink-900); border: 1px solid var(--ink-600); border-radius: 3px;
    padding: 10px 14px; color: var(--text); font-family: var(--body); font-size: 14px;
    flex: 1; min-width: 200px;
  }}
  input:focus {{ outline: none; border-color: var(--brass); }}
  button {{
    font-family: var(--body); border: 1px solid var(--brass); border-radius: 3px; padding: 10px 20px;
    font-weight: 600; cursor: pointer; background: var(--brass); color: var(--ink-900);
  }}
  button:hover {{ background: var(--brass-bright); border-color: var(--brass-bright); }}
</style>
</head>
<body>
  <div class=\"sheet\">
    <p class=\"eyebrow\">Quill / shortener</p>
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
