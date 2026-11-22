# Scripts and green flags

A Kitty file becomes a Scratch target. A plain file becomes a sprite named
after the file unless it also creates a class or decorated target.

## Make a block run on the green flag

```python
import kitty

@kitty.green_flag
def start():
    kitty.say("Hello!")
```

This becomes a `when green flag clicked` hat block. The code inside `start`
runs when the player clicks the green flag.

Each function can have one hat. Two functions with different hats run as
separate Scratch scripts.

## Top-level code

Code outside a function is placed in a green-flag script:

```python
import kitty

kitty.say("Hello!")
kitty.move(10)
```

Top-level code and a `@kitty.green_flag` function are separate scripts.
Scratch may run both scripts at nearly the same time.

## Call kitty blocks

Use `kitty` before a Scratch block:

```python
import kitty

kitty.say("Hello")
kitty.move(10)
```

You can also import a block directly:

```python
from kitty import say

say("Hello")
```

## Call blocks inside a sprite class

Inside `kitty.Sprite`, call the same blocks through `self`:

```python
import kitty

class Cat(kitty.Sprite):
    @kitty.green_flag
    def start(self):
        self.say("Hello!")
        self.move(10)
```

`self.say(...)` and `kitty.say(...)` create the same kind of Scratch block.
Use `self` for state and blocks owned by that sprite.

## Statements that belong inside a function

Put repeated or conditional behavior inside a function or hat:

```python
@kitty.green_flag
def start():
    for _ in range(4):
        kitty.move(25)
        kitty.turn_right(90)
```

Do not place an ordinary custom block call between declarations and define
other blocks without understanding the target. Read [functions](functions.md)
before using larger programs.
