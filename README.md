# Kitty

Kitty is a Python library and compiler for creating Scratch 3 projects.

Write Python syntax directly. Use normal variables, functions, conditionals,
lists, dictionaries, `for` loops, and `while` loops. Use `kitty` for blocks
that are specific to Scratch.

Kitty source is compiled into an `.sb3` file. It is not interpreted by the
Python runtime when the resulting Scratch project runs.

## Example

```python
import kitty

score = 0

@kitty.green_flag
def start():
    global score

    while True:
        kitty.move(10)
        score += 1

        if kitty.touching("edge"):
            break
```

The same Python constructs used outside Kitty are preferred:

```python
names = ["Ada", "Lin", "Sam"]

for name in names:
    if name == "Ada":
        continue
    kitty.say("Hello " + name)
```

```python
@kitty.number
def double(value):
    return value * 2

kitty.say(double(4))
```

## Language mapping

| Python syntax | Kitty behavior |
| --- | --- |
| `while True:` | Forever loop |
| `break` | Exit the current loop |
| `continue` | Skip to the next loop pass |
| `for item in items:` | Iterate over a list or dictionary |
| `for i in range(10):` | Repeat ten times |
| `if` / `elif` / `else` | Conditional execution |
| `def name(...):` | Named function or custom block |
| `return value` | Return a number or text value |

| Kitty API | Scratch operation |
| --- | --- |
| `kitty.move(10)` | Move ten steps |
| `kitty.say("Hello")` | Say text |
| `kitty.touching("edge")` | Edge sensing |
| `kitty.broadcast("message")` | Broadcast a message |
| `kitty.switch_costume("name")` | Switch costume |
| `kitty.create_clone()` | Create a clone |

## Python-only helpers

Use `@ignore` for code that Python libraries provide but Kitty
cannot compile into Scratch:

```python
import numpy

@ignore
def average(values):
    return numpy.mean(values)
```

Kitty emits a warning that `numpy` cannot be compiled and omits the function
from the `.sb3`. Do not call an ignored function from code that runs in Scratch;
that is a compile error.

## Compile

### Install

```bash
pip install kitty-scratch
```

After installation, keep `import kitty` in source files and use the
Python module first:

```bash
py -m kitty build script.py
py -m kitty build cat.py mouse.py -o game.sb3
py -m kitty build folder/
py -m kitty compile game.py
py -m kitty comp game.py
py -m kitty decompile game.sb3
```

`kitty build`, `kitty compile`, `kitty comp`, and `kitty decompile` are also
available as convenience commands after Windows creates their launch shims.

On systems where `py` is unavailable, use `python -m kitty` instead.

### Windows launcher setup

The first Kitty CLI invocation automatically creates Windows command shims in
`%LOCALAPPDATA%\Microsoft\WindowsApps`:

- `kitty`
- `kitty-build`
- `kitty-decomp`

No Python `Scripts` directory or manual `PATH` edit is required. Open a new
terminal and verify:

```powershell
py -m kitty --help
py -m kitty comp tests/project
```

Open a new terminal only if you want to use the convenience commands:

```powershell
kitty version
```

For maintainers, see [Testing and publishing a release](docs/releasing.md).

Documentation is maintained on the
[GitHub Kitty Wiki](https://github.com/pi-3-14159265/kitty/wiki).

```bash
py -m kitty build cat.py mouse.py -o game.sb3
py -m kitty build folder/
```

One source file produces an adjacent `.sb3` file. Multiple source files
produce `project.sb3` by default. Use `-o` to select an output name. A
directory compiles eligible `.py` files directly inside that directory.

## Documentation

- [Getting started](docs/getting-started.md)
- [Python control flow](docs/choices-and-loops.md)
- [Scripts and functions](docs/functions.md)
- [Values, lists, and dictionaries](docs/values-and-math.md)
- [Sprites and targets](docs/sprites.md)
- [API reference](docs/reference.md)
- [Limitations](docs/limitations.md)

Project and maintainer links:

- [GitHub repository](https://github.com/pi-3-14159265/kitty)
- [GitHub documentation Wiki](https://github.com/pi-3-14159265/kitty/wiki)
- [Issue tracker](https://github.com/pi-3-14159265/kitty/issues)
- Maintainer: [Thayaden Pi](mailto:thayaden_pi@proton.me)
