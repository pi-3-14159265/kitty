# Turn a Scratch project into Python

`kitty decomp` reads a Scratch `.sb3` file and writes a folder of Kitty Python
that `kitty build` turns back into the same project.

```bash
kitty decomp game.sb3
kitty decomp game.sb3 my_game
```

`kitty decompile` is the same command. With no folder name, `game.sb3` becomes
`game/`. The folder must be new or empty, so a decompile never writes over
Python you have changed.

## What you get

```text
game/
    Assets/
        cat-a.svg
        cat-b.svg
        blue sky.png
    Sounds/
        Meow.wav
    stage.py
    Cat.py
    Ball.py
    blocksAsText.txt
```

- `Assets/` holds every costume and backdrop. An image two sprites share is written once.
- `Sounds/` holds every sound.
- `stage.py` is the stage: its backdrops, the variables and lists for all sprites, and the stage's scripts.
- Each sprite gets its own file, named after the sprite. A name that cannot be a file name, or one Kitty keeps for itself (`stage`, `kitty`, `comp`, `decomp`, `cli`), gets another file name, and the file keeps the sprite's name with `kitty.sprite_name(...)`.
- `blocksAsText.txt` writes every script out as Scratch blocks, to read next to the Python.

## Build it again

```bash
kitty build game/ -o game2.sb3
```

Change the Python, build, and open the `.sb3` in Scratch.

## A sprite file

```python
# Sprite Cat, decompiled from game.sb3 by kitty decomp.
import kitty

kitty.costume("Assets/cat-a.svg", center=(48, 50))
kitty.costume("Assets/cat-b.svg", center=(46, 53))
kitty.sound("Sounds/Meow.wav")
kitty.start_with(x=-100, y=20, size=80, layer=2)

score = kitty.variable("score", 0, shared=True)
lives = 3
bag = kitty.list("bag", ["apple"], scratch=True)


@kitty.block(warp=False)
def jump(height):
    for _ in range(10):
        kitty.change_y(height)


@kitty.green_flag
def on_green_flag():
    global lives
    lives = 3
    while not kitty.touching("edge"):
        kitty.move(10)
        if kitty.key_pressed("space"):
            jump(5)
    bag.append(kitty.join("lives ", lives))
```

- `center=` is the point of the image that sits on the sprite's x and y. It is written when the costume's center in Scratch is not the middle of the image. See [kitty.costume](costumes-sounds-and-names.md#kittycostume).
- `resolution=2` is written for bitmaps Scratch saved at double size. See [Drawn at double size](costumes-sounds-and-names.md#drawn-at-double-size).
- `kitty.start_with(...)` is how the sprite starts when the project opens: where it is, its size, its costume, whether it shows, and its layer. See [kitty.start_with](costumes-sounds-and-names.md#kittystart_with).
- A variable for all sprites lives in `stage.py`. A sprite file that uses it declares it again with `shared=True` and the same starting value, and both files use the one variable. See [Sprites](sprites.md#sprites).
- A Scratch list becomes `kitty.list(..., scratch=True)`: the items stay in that one Scratch list.
- `global` names the variables a function changes. See [Names and scope](names-and-scope.md).

## How blocks become Python

| Scratch | Kitty Python |
| --- | --- |
| when green flag clicked | `@kitty.green_flag` on a function |
| when [space] key pressed | `@kitty.when_key("space")` |
| when I receive [go] | `@kitty.when_receive("go")` |
| define jump (height) | `def jump(height):` |
| custom block without "Run without screen refresh" | `@kitty.block(warp=False)` |
| a boolean input | `def jump(height, high: bool):` |
| repeat (10) | `for _ in range(10):` |
| forever | `while True:` |
| if, else, and an if inside else | `if`, `else`, and `elif` |
| repeat until <touching edge?> | `while not kitty.touching("edge"):` |
| set [score] to (0) | `score = 0` |
| change [score] by (1) | `score += 1` |
| item (1) of [bag] | `bag[0]` |
| item (i) of [bag] | `bag[i - 1]` |
| item # of (x) in [bag] | `bag.index(x) + 1` |
| insert (x) at (1) of [bag] | `bag.insert(0, x)` |
| delete (1) of [bag] | `bag.pop(0)` |
| (bag), the list as text | `kitty.join(bag, "")` |
| join (a) (b) | `kitty.join(a, b)` |
| ([sqrt] of (9)) | `kitty.sqrt(9)` |
| ([x position] of [Cat]) | `kitty.property_of("x position", "Cat")` |

Scratch counts list items from 1, and Python from 0, so item 1 is `bag[0]`.
`sin`, `cos`, and the other Scratch math blocks keep working in degrees:
`kitty.sin(90)` is 1.

A Scratch name that is not a Python name, such as `my score`, becomes
`my_score`, and the declaration keeps the Scratch name:
`my_score = kitty.variable("my score", 0)`.

## What stays a comment

Kitty has no Python for some blocks. The decompiler keeps each one as a
comment where it was, and warns about it:

```text
warning: sprite Cat: music_playDrumForBeats has no Kitty block
```

```python
    # Not decompiled, music_playDrumForBeats has no Kitty block:
    #     play drum [1 v] for (0.25) beats
```

- Blocks from extensions other than Pen, such as Music, Video Sensing, and Text to Speech.
- A broadcast whose message is a block, not typed text.
- A `when loudness >` or `when timer >` hat whose value is a block.
- Scripts with no hat block. Scratch never runs them either.

Scratch comments become Python comments.

## What changes after a rebuild

- A cloud variable becomes an ordinary variable.
- `bag[i - 1]` with `i` at 0 or below counts from the end of the list in Kitty. Scratch gives nothing for item 0.
- Monitors that showed come back at the top-left of the stage.
- A custom block's inputs move to the end of its label: `jump (5) high` becomes `jump high (5)`.
- Kitty adds its own blocks, variables, and lists to run custom blocks, such as the block `jump run` and the list `jump height`, which holds each call's input. See [What you see in Scratch](functions.md#what-you-see-in-scratch).
- Decompiling a project that Kitty built gives back those inner blocks too, not your original Python. Keep your `.py` files.
