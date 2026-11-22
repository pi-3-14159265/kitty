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

## Compile

```bash
python comp.py script.py
python comp.py cat.py mouse.py -o game.sb3
python comp.py folder/
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
