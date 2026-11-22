# Kitty

**Kitty helps you move from Scratch to Python while keeping the same fun, visual
Scratch blocks.**

Scratch is a great place to learn programming. Kitty keeps familiar ideas
such as sprites, blocks, variables, loops, costumes, and broadcasts, but lets
you write them in Python. Kitty reads your Python-like script and turns it into
a Scratch 3 `.sb3` project. It does **not** run your script normally in Python.

## Your first Kitty project

Create a file named `cat.py`:

```python
import kitty

score = 0

@kitty.green_flag
def start():
    global score
    kitty.say("Hello!")
    kitty.move(10)
    score += 1
    kitty.say(score)
```

Compile it:

```bash
python comp.py cat.py
```

Open `cat.sb3` in Scratch. Click the green flag. The Cat sprite will say
hello, move 10 steps, set `score` to `1`, and say `1`.

## Scratch block, Kitty code

| Scratch idea | Kitty code |
| --- | --- |
| When green flag clicked | `@kitty.green_flag` |
| Say Hello! | `kitty.say("Hello!")` |
| Move 10 steps | `kitty.move(10)` |
| Change x by 10 | `kitty.change_x(10)` |
| Repeat 10 | `for _ in range(10):` |
| If on edge, bounce | `kitty.if_on_edge_bounce()` |
| Create a variable | `score = 0` |
| Change a variable by 1 | `score += 1` |
| Broadcast a message | `kitty.broadcast("go")` |

## Tiny examples

### Move and turn

```python
import kitty

@kitty.green_flag
def start():
    for _ in range(10):
        kitty.move(10)
        kitty.turn_right(90)
```

### Repeat only while a key is not pressed

```python
import kitty

@kitty.green_flag
def start():
    while not kitty.key_pressed("space"):
        kitty.move(3)
```

### Work with a list

```python
import kitty

names = ["Ada", "Lin", "Sam"]

@kitty.green_flag
def start():
    for name in names:
        kitty.say("Hello " + name)
```

### Make a second sprite

Put separate sprites in separate files:

```python
# cat.py
import kitty

@kitty.green_flag
def start():
    kitty.say("I am Cat!")
```

```python
# mouse.py
import kitty

@kitty.green_flag
def start():
    kitty.say("I am Mouse!")
```

Compile both files together:

```bash
python comp.py cat.py mouse.py -o game.sb3
```

## Compile and open

```bash
python comp.py script.py
python comp.py stage.py cat.py -o game.sb3
python comp.py folder/
```

Each project needs at least one eligible `.py` file. One file creates
`script.sb3` beside that file. Multiple files create `project.sb3` unless
`-o` names an output. Kitty compiles only `.py` files directly inside a
directory; it does not search subfolders.

For complete instructions, see the [documentation](docs/README.md).

## Learn the language

- Start with [Your first project](docs/getting-started.md).
- Learn [scripts and green flags](docs/scripts.md).
- Learn [choices and loops](docs/choices-and-loops.md).
- Learn [lists](docs/lists.md), [dictionaries](docs/dictionaries.md), and
  [functions](docs/functions.md).
- See the [complete block reference](docs/reference.md).

## Development

Run the built-in compile and rejection tests:

```bash
python tests/run.py
```
