# Quill

A general-purpose scripting language: classes with inheritance, exceptions,
closures, a module system, and a real standard library — not a toy anymore.
Python-style indentation, dynamically typed, built in Python as a
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

### Variables, printing, and control flow

```
let name = "world"
print(f"Hello, {name}!")     # f-strings interpolate {expr}; plain "..." doesn't

if score > 90:
    print("A")
elif score > 80:
    print("B")
else:
    print("C")

# one-liner form works too, same as Python:
if x > 0: print("positive")
else: print("non-positive")

let i = 0
while i < 5:
    print(i)
    i += 1              # augmented assignment: += -= *= /=

for x in [1, 2, 3]:
    print(x)
for n in range(1, 21):
    if n % 15 == 0:
        print("FizzBuzz")
```

`let` declares a new variable; plain `name = value` assigns to an *existing*
one. Declaring first is required — it catches typos early, and it's what
lets closures mutate a captured variable with no special keyword needed
(see below).

### Functions and closures

```
pull add(a, b):
    return a + b

pull make_counter():
    let count = 0
    pull increment():
        count = count + 1     # mutates the captured `count` directly
        return count
    return increment

let counter = make_counter()
print(counter())   # 1
print(counter())   # 2
```

`pull` is the function-definition keyword (an original choice rather than
`def`/`fn`). Functions are values (`let double = pull(x): return x * 2`),
including as inline arguments — `xs.map(pull(x): return x * x)` works because
a single-line function body (`pull(...): <one statement>`) doesn't need
indentation at all, which also happens to be the only way an anonymous
function can have a body while nested inside a call's parentheses in the
first place.

### Classes

```
class Animal:
    pull init(name):
        self.name = name
    pull speak():
        return f"{self.name} makes a sound"

class Dog(Animal):
    pull init(name, breed):
        super.init(name)
        self.breed = breed
    pull speak():
        return f"{self.name} the {self.breed} barks"

let rex = Dog("Rex", "Labrador")
print(rex.speak())    # Rex the Labrador barks
print(type(rex))      # Dog
```

Single inheritance, `super.method(...)` calls the parent's version (works
correctly through arbitrarily deep chains, not just one level). No `self`
parameter to declare — it's bound automatically inside methods.

### Exceptions

```
try:
    let result = risky_operation()
except e:
    print(f"something went wrong: {e}")
finally:
    print("cleanup always runs")

raise "custom error message"
```

`except` catches both your own `raise`d values *and* built-in runtime errors
(division by zero, bad index, wrong argument count, etc.) — the caught value
is the error message string for built-in errors, or whatever value you
passed to `raise` for your own. `finally` always runs, including when the
`try` block returns or an exception isn't caught at all.

### Modules

```
# mathutils.ql
let VERSION = "1.0"
pull square(x):
    return x * x
```
```
# main.ql
import "mathutils.ql" as mu
print(mu.VERSION)
print(mu.square(5))
```

Paths are resolved relative to the importing file.

### Data types and method-call syntax

- Numbers: `5`, `3.14` (int/float unify automatically; `/` always gives a
  float, `//` gives floor division). Whole-number floats print without a
  trailing `.0` (`sqrt(16)` shows `4`, not `4.0`).
- Strings: `"text"` is always a literal - it never interpolates, even if it
  contains `{...}`. Prefix it with `f` (`f"text {expr}"`) to interpolate,
  matching real Python's f-string convention exactly. Both forms support
  `\n`/`\t`/`\"` escapes and methods: `.upper()` `.lower()` `.trim()`
  `.split(sep)` `.replace(a, b)` `.contains(s)` `.starts_with(s)`
  `.ends_with(s)` `.find(s)` `.repeat(n)` `.title()`
- `true` / `false` / `nil`
- Lists: `[1, 2, 3]`, indexed with `xs[0]`/`xs[-1]`, with methods:
  `.push(x)` `.pop()`/`.pop(i)` `.sort()` `.reverse()` `.contains(x)` `.index_of(x)`
  `.join(sep)` `.map(f)` `.filter(f)` `.reduce(f, init)` (`.sort()` and
  `.reverse()` return a new list rather than mutating, matching the
  standalone `sorted()`)
- Maps: `{"key": "value"}`, indexed with `m["key"]` or `m.key`, with methods:
  `.keys()` `.values()` `.items()` `.has(k)` `.get(k, default)`
- Ternary expression: `"big" if x > 5 else "small"`

### Built-in functions

`print`, `len`, `type`, `str`, `num`, `bool`, `range`, `input`, `push`, `pop`,
`keys`, `values`, `items`, `has`, `sorted`, `sum`, `min`, `max`, `abs`,
`round`, `slice`, `sqrt`, `floor`, `ceil`, `enumerate`, `zip`, `read_file`,
`write_file`, `file_exists`, plus the constant `PI`. (The older top-level
`push`/`pop`/`keys`/etc. and the newer `.push()`/`.pop()`/`.keys()` method
forms both work and do the same thing — the methods are just nicer to chain.)

## What's deliberately not here yet

Multiple inheritance, operator overloading, a package manager / third-party
libraries, async/concurrency, static typing. All reasonable next steps if
this keeps growing — left out to keep what's here solid and well-tested
rather than spreading thinner.

## Project layout

```
quill/
  lexer.py          # tokenizer - tracks indentation (INDENT/DEDENT tokens),
                     # the trickiest part, plus string interpolation
  tokens.py         # token types
  ast_nodes.py      # AST node dataclasses
  parser.py         # recursive-descent parser with precedence climbing
  environment.py    # scope chain (this is what makes closures work)
  interpreter.py    # tree-walking evaluator: control flow, classes,
                     # exceptions, imports, method dispatch
  values.py         # runtime value types (QuillClass, QuillInstance,
                     # bound methods) and formatting/equality helpers
  methods.py        # built-in method tables for strings/lists/maps
  builtins.py       # top-level built-in functions
  cli.py            # `quill script.ql` / `quill` REPL
examples/           # hello, fib, closures, collections, fizzbuzz, classes,
                     # exceptions, methods_and_ops, mathutils + import_demo
apps/tasks/         # a real small app, not just a demo script - see below
tests/              # 52 tests across the lexer and interpreter end-to-end
```

## A real app, not just demo scripts

[`apps/tasks/`](apps/tasks/) is a small interactive, persistent task manager
written entirely in Quill:

```powershell
cd apps\tasks
quill main.ql
```

It's the thing that actually proved classes, modules, file I/O, and
exceptions work together, not just individually in isolated examples -
testing it interactively (piping a full scripted menu session into `quill`
rather than only running non-interactive scripts) found a real bug: PowerShell
prepends a UTF-8 BOM to piped stdin, which was landing on the first
`input()` call of any session and silently breaking its first `==`
comparison. Fixed in the `input()` builtin itself. `list.pop()` also gained
an optional index argument (`xs.pop(i)`) because removing a task by number
needed it and the language didn't have it yet. See
[`apps/tasks/README.md`](apps/tasks/README.md) for the details.

Every feature described above was actually run through the interpreter while
building it, not just written and assumed to work. That process caught two
real bugs worth knowing about if you're extending this: (1) a duplicated
token-consumption bug in the class-body parser that broke every method
definition, found by running the first classes example; (2) `raise`d
exceptions not inheriting from the same base error class as everything else,
which meant an uncaught `raise` would crash the CLI with a raw Python
traceback instead of a clean message — found by deliberately testing that
exact scenario rather than assuming the happy-path tests covered it.
