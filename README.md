# Quill

A small, friendly, general-purpose scripting language. Python-style indentation
for blocks, dynamically typed, closures that just work, built in Python as a
tree-walking interpreter.

The name's a placeholder — trivial to rename later (it's just the string
`"quill"` in `pyproject.toml` and the `quill/` package directory).

## Install

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .
```

This installs a `quill` command. Run it globally from any terminal instead by
installing with `pipx install C:\path\to\quill-lang` (see the osint-toolkit
project's README for the full pipx walkthrough if you want that).

## Usage

```powershell
quill                  # start the REPL
quill script.ql        # run a script
```

## The language

### Variables and printing

```
let name = "world"
print("Hello, {name}!")     # string interpolation with {expr}
print("2 + 2 = {2 + 2}")
```

`let` declares a new variable. Plain `name = value` (no `let`) assigns to an
*existing* variable — declaring first is required, which catches typos early
and is what makes closures able to mutate a captured variable without any
special keyword (see below).

### Functions and closures

```
fn add(a, b):
    return a + b

fn make_counter():
    let count = 0
    fn increment():
        count = count + 1     # mutates the captured `count`, no special syntax needed
        return count
    return increment

let counter = make_counter()
print(counter())   # 1
print(counter())   # 2
```

Functions are values — `let f = fn(x): return x * 2` works too, for passing
callbacks around.

### Control flow

```
if score > 90:
    print("A")
elif score > 80:
    print("B")
else:
    print("C")

let i = 0
while i < 5:
    print(i)
    i = i + 1

for x in [1, 2, 3]:
    print(x)

for n in range(1, 21):
    if n % 15 == 0:
        print("FizzBuzz")
```

`break` and `continue` work inside `while`/`for`. `for` iterates lists,
strings (character by character), and maps (over their keys).

### Data types

- Numbers: `5`, `3.14` (int/float unify automatically, `/` always gives a float)
- Strings: `"text"`, with `{expr}` interpolation and `\n`/`\t`/`\"` escapes
- `true` / `false` / `nil`
- Lists: `[1, 2, 3]`, indexed with `xs[0]` or `xs[-1]` (negative = from the end)
- Maps: `{"key": "value"}`, indexed with `m["key"]`

Truthiness follows the usual scripting-language intuition: `nil`, `false`,
`0`, `""`, `[]`, and `{}` are falsy; everything else is truthy.

### Built-in functions

`print`, `len`, `type`, `str`, `num`, `bool`, `range`, `input`, `push`, `pop`,
`keys`, `values`, `items`, `has`, `sorted`, `sum`, `min`, `max`, `abs`,
`round`, `slice`. Collections use functions rather than methods
(`push(list, x)`, not `list.push(x)`) — this keeps the interpreter simple
for now; method-call sugar is a natural thing to add later.

## What's deliberately not here yet

No classes/structs, no modules/imports, no exception handling (`try`/`catch`),
no floor division. All of these are reasonable next steps, left out of v1 to
keep the core (functions, closures, control flow, collections, clear error
messages) solid and well-tested first rather than spreading thin.

## Project layout

```
quill/
  lexer.py          # tokenizer - handles indentation (INDENT/DEDENT), the
                     # trickiest part, plus string interpolation
  tokens.py         # token types
  ast_nodes.py      # AST node dataclasses
  parser.py         # recursive-descent parser with precedence climbing
  environment.py    # scope chain (this is what makes closures work)
  interpreter.py    # tree-walking evaluator
  values.py         # runtime value helpers (truthiness, equality, printing)
  builtins.py       # built-in functions
  cli.py            # `quill script.ql` / `quill` REPL
examples/           # hello.ql, fib.ql, closures.ql, collections.ql, fizzbuzz.ql
tests/              # 26 tests across the lexer and the interpreter end-to-end
```

Every example in `examples/` and every behavior described above was actually
run through the interpreter while building this, not just written and assumed
to work — including deliberately triggering errors (undefined variable,
division by zero, type mismatch, out-of-range index, wrong argument count) to
confirm they produce a clean message with a line number instead of a raw
Python traceback.
