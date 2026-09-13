# Quill Tasks

A small interactive, persistent task manager. A real (if simple) application
written entirely in Quill.

```powershell
cd apps\tasks
quill main.ql
```

Tasks are saved to `tasks.txt` next to the script and reloaded automatically
next time you run it.

## What it exercises

- **Classes** (`task.ql`): `Task` with fields, methods, and a `to_string()`
  used for display.
- **Modules**: `main.ql` imports `task.ql` for both the class and a
  `task_from_line()` parser function.
- **File I/O + a hand-rolled serialization format**: tasks round-trip through
  `read_file`/`write_file` as `done::priority::title` lines.
- **Exceptions**: picking a task number that doesn't exist raises a plain
  string error, caught by the menu loop's `try`/`except` and shown as a
  normal message instead of crashing the program.
- **Interactive I/O**: the whole thing is a `while` loop around `input()`.

## A real bug this app found in the language itself

Testing this interactively (piping a scripted sequence of menu choices into
`quill main.ql` to simulate a full session, rather than only running
non-interactive example scripts) surfaced a real bug: PowerShell prepends a
UTF-8 BOM character to piped stdin, which was landing on the very first
`input()` call of any session and silently breaking its first `==`
comparison (`choice == "1"` failed because the actual string was
`"﻿1"`). Fixed by stripping a leading BOM in the `input()` builtin
itself — the same category of fix as an earlier BOM bug in the lexer, just
showing up at runtime instead of parse time.

`list.pop()` also gained an optional index argument (`xs.pop(i)`, Python's
`list.pop([index])` convention) while building this — removing a task by
number needed it and the language didn't have it yet.
