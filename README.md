# Quill

A general-purpose scripting language with classes and inheritance, exceptions,
closures, a module system, and a real standard library. Python-style
indentation, dynamically typed, built in Python as a tree-walking
interpreter.

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

Single inheritance. `super.method(...)` calls the parent's version and
resolves correctly through arbitrarily deep chains. No `self` parameter to
declare; it's bound automatically inside methods.

### Operator overloading

```
class Vec:
    pull init(x, y):
        self.x = x
        self.y = y
    pull __add__(other):
        return Vec(self.x + other.x, self.y + other.y)
    pull __eq__(other):
        return self.x == other.x and self.y == other.y
    pull __str__():
        return f"Vec({self.x}, {self.y})"

print(Vec(1, 2) + Vec(3, 4))    # Vec(4, 6)
print(Vec(1, 2) == Vec(1, 2))   # true
```

A class defines `__add__` `__sub__` `__mul__` `__div__` `__floordiv__` `__mod__`
`__pow__` `__eq__` `__lt__` `__gt__` `__le__` `__ge__` `__neg__` `__str__` the
same way Python does, and the matching operator calls it. Two things worth
knowing: the overload only fires when the *instance* is the left-hand operand
(no `__radd__`-style reflected operators yet), and `__eq__`/`__lt__`/etc.
always come back as a real `true`/`false` even if the method itself returns
something else, so a sloppy implementation can't leak a non-boolean out
through `==`. A class with no `__str__` still prints as `<ClassName instance>`,
exactly as before this feature existed.

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
- Comprehensions: `[x * x for x in xs if x > 0]`, `{k: v.upper() for k, v in m.items()}`,
  chaining multiple `for`/`if` clauses works the same as Python's does:
  `[x + y for x in [1, 2] for y in [10, 20] if x != y]`
- Destructuring: `let a, b = [1, 2]` unpacks a list into two new names; drop
  `let` to reassign existing ones (`a, b = [b, a]` swaps them); and
  `for k, v in m.items(): ...` unpacks each pair on every iteration instead
  of indexing it apart by hand.

### Built-in functions

`print`, `len`, `type`, `str`, `num`, `bool`, `range`, `input`, `push`, `pop`,
`keys`, `values`, `items`, `has`, `sorted`, `sum`, `min`, `max`, `abs`,
`round`, `slice`, `sqrt`, `floor`, `ceil`, `enumerate`, `zip`, `read_file`,
`write_file`, `file_exists`, `serve`, `url_encode`, `json_encode`,
`json_decode`, `sha256`, `random`, `random_int`, `random_choice`, `shuffle`,
`env_get`, `http_get`, `http_post`, plus the constant `PI`. (The older top-level `push`/`pop`/`keys`/etc.
and the newer `.push()`/`.pop()`/`.keys()` method forms both work and do the
same thing — the methods are just nicer to chain.)

`json_encode`/`json_decode` map directly onto Quill's own runtime values
(lists, maps, strings, numbers, bools, nil are already exactly what Python's
`json` module expects) - the one thing they can't handle is a class instance,
which needs converting to a plain map first. `sha256` is there specifically
so passwords/API keys never need to be compared or stored as plaintext - see
`apps/website/`'s `/api/wipe` route for the actual pattern. `random`/
`random_int`/`random_choice`/`shuffle` and `env_get` (for reading
config/secrets from the environment instead of hardcoding them) round out
what a real backend needs.

`http_get(url, [headers])` and `http_post(url, body, [headers])` are the
outbound side of the same story `serve()` covers inbound - both return
`{"status": ..., "body": ..., "headers": {...}}`, and both raise a clear
`http_get()/http_post() failed: ...` error rather than a raw traceback when
the host is unreachable. `http_post`'s `body` can be a map (form-encoded
automatically, with `Content-Type` set to match) or a plain string.

## What's deliberately not here yet

Multiple inheritance, reflected operators (`__radd__`-style), a package
manager / third-party libraries, async/concurrency, static typing. All
reasonable next steps if this keeps growing — left out to keep what's here
solid and well-tested rather than spreading thinner.

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
apps/tasks/         # a real CLI app, built to prove the language - see below
apps/website/       # the same app, but as an actual website
apps/guess_game/    # number-guessing game, CLI
apps/password_gen/  # password generator, CLI
apps/adventure/     # small text-adventure, CLI
apps/shortener/     # URL shortener, website
tests/              # 80 tests across the lexer and interpreter end-to-end
```

## Real apps

[`apps/tasks/`](apps/tasks/) is a small interactive, persistent task manager
written entirely in Quill:

```powershell
cd apps\tasks
quill main.ql
```

It's what proved classes, modules, file I/O, and exceptions actually hold
together in a real program instead of six separate isolated examples.
Testing it interactively - piping a full scripted menu session into `quill`
instead of only running scripts non-interactively - found a real bug:
PowerShell prepends a UTF-8 BOM to piped stdin, and it was landing on the
first `input()` call of any session and silently breaking its first `==`
comparison. Fixed in the `input()` builtin itself. `list.pop()` also gained
an optional index argument (`xs.pop(i)`) because removing a task by number
needed it and the language didn't have it yet. See
[`apps/tasks/README.md`](apps/tasks/README.md) for the details.

[`apps/website/`](apps/website/) is the same task manager as an actual
website instead of a terminal app:

```powershell
cd apps\website
quill site.ql
```
then open `http://127.0.0.1:8080/` in a browser. Quill had no networking at
all before this, so it now has a `serve(port, handler)` builtin (Python's
`http.server` underneath, a plain Quill function on top). Building the
page's embedded CSS also exposed a real gap: f-strings had no way to write a
literal `{` or `}`, so every CSS rule was getting misread as an
interpolation. Fixed with real brace-escaping (`{{`/`}}`, matching Python's
own f-string convention).

It also has a `GET /api/tasks` JSON endpoint and a `POST /api/wipe` route
gated by a hashed admin key - `sha256()`, comparing hashes rather than
plaintext - see [`apps/website/README.md`](apps/website/README.md) for both.

[`apps/guess_game/`](apps/guess_game/) and [`apps/password_gen/`](apps/password_gen/)
are two short, self-contained CLI programs (`quill game.ql`, `quill gen.ql`)
that exercise `random`/`random_int`/`sha256` outside of a test harness. The
guess game found a real bug in its own design: piping a finite amount of
input into a `while true` loop means `input()` eventually hits EOF and
returns `""` forever, so a naive "keep asking until you get a number" loop
spins forever once stdin runs dry. Fixed at the app level with a bad-guess
counter that gives up after five consecutive unreadable answers, without
changing what `input()` does at EOF (other apps rely on it returning `""`).

[`apps/adventure/`](apps/adventure/) is a small text-adventure (three rooms,
one locked door, one item that ends the game) leaning on classes, maps as a
room→exit graph, and comprehensions for filtering inventory and exits.
Writing it surfaced a real lexer trap: Quill has no single-quote string
syntax at all, so `xs.join(', ')` - easy to type out of Python habit - fails
inside an f-string's `{...}`, because that interpolated fragment gets
re-tokenized on its own and the bare `'` is unrecognized. Using `"..."`
there instead fixes it; a regression test locks it in.

[`apps/shortener/`](apps/shortener/) is a URL shortener website, the same
shape as `apps/website/`: `POST /shorten` generates a random code and
persists the mapping as JSON, `GET /<code>` redirects, `GET /api/links`
returns the raw map. Proved out against a live running instance rather than
just read over on the page - shortened a real URL, followed the redirect,
and confirmed an unknown code 404s instead of crashing the server.

Every feature described above ran through the interpreter for real while it
was being built. That process caught two real bugs worth knowing about if
you're extending this: a duplicated token-consumption bug in the class-body
parser that broke every method definition, found by running the first
classes example, and `raise`d exceptions not inheriting from the same base
error class as everything else, which meant an uncaught `raise` crashed the
CLI with a raw Python traceback instead of a clean message. Both turned up
by deliberately testing the exact scenario rather than assuming the
happy-path tests covered it.
