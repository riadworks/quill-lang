# Quill Language Support for VS Code

Syntax highlighting for `.ql` files: keywords, `pull`/`class` declarations,
strings (including `f"..."` interpolation), comments, and numbers.

## Installing (no publishing, no build step)

This extension isn't published to the Marketplace - it's plain source, so
VS Code can load it directly:

1. Open the Command Palette (`Ctrl+Shift+P`).
2. Run **Developer: Install Extension from Location...**
3. Pick this `editors/vscode` folder.
4. Reload the window. Any `.ql` file now highlights as Quill.

(Alternatively, copy or symlink this folder into your VS Code extensions
directory - `%USERPROFILE%\.vscode\extensions\` on Windows, `~/.vscode/extensions/`
on macOS/Linux - under a name like `quill-lang-0.1.0`, then reload.)

## Live error checking (optional, separate from this extension)

This extension is highlighting only. For live syntax-error diagnostics as
you type, Quill ships its own minimal language server - point any generic
LSP client extension (search the Marketplace for "Generic LSP Client") at:

- **Command**: `quill`
- **Arguments**: `lsp`
- **Language ID**: `quill`
- **File extension**: `.ql`

It reports exactly one thing - whether the file parses, and where the first
error is - nothing fancier (no completion, no hover, no go-to-definition).
