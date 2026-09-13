pull load_links(path):
    try:
        let raw = read_file(path)
        return json_decode(raw)
    except e:
        return {}

pull save_links(path, links):
    write_file(path, json_encode(links))

pull make_code(links):
    let alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    while true:
        let code = ""
        for i in range(0, 6):
            let idx = random_int(0, len(alphabet) - 1)
            code = code + alphabet[idx]
        if not has(links, code):
            return code
