# Limitations and troubleshooting

Kitty is a Scratch compiler, not a complete Python interpreter. This page
lists the limits that matter most.

## Imports

Supported compiled imports are `kitty` and `math`:

```python
import kitty
import math
from math import sin
```

Third-party modules are allowed only inside `@ignore` Python-only
functions. A third-party import produces a compile warning:

```text
warning: numpy imported and cannot be compiled
```

An ignored function is omitted from the Scratch project. It must not be called
from code that Kitty translates into a Scratch script, or compilation fails.

## Python values

Kitty supports numbers, text, booleans, one-dimensional lists, rectangular
grids, dictionaries, tuples, and sets.

These are not ordinary Python objects:

- Lists and dictionaries share references in some forms.
- Grids must be rectangular.
- Sets keep unique values.
- Tuples cannot be changed in place.
- Slice assignment is not supported.

## Files and output

For multiple input scripts or a directory with multiple files, the default
output is `project.sb3`. For one input script, the default is a `.sb3` file
beside that script.

Use `-o` to choose an output name:

```bash
kitty build cat.py mouse.py -o game.sb3
```

A directory scan is not recursive.

## Scratch exceptions

`try` and `except` catch only `raise` statements written in Kitty source.
Scratch runtime errors such as bad list indexes, division by zero, missing
dictionary keys, and unknown names do not become Python exceptions.

## Backdrops and costumes

Paths are relative to the `.py` file that adds the media.

```python
kitty.costume("cat.svg")
kitty.backdrop("beach.svg")
kitty.sound("meow.wav")
```

Costume declarations do not belong inside a loop. A backdrop belongs on the
stage, in `stage.py`, or on a `kitty.Stage` class.

## Class and sprite limits

- Constructor arguments can be numbers, text, or lists.
- A project can have only one stage.
- Hat functions cannot accept parameters.
- The first method parameter must be named `self`.
- Scratch clones share one sprite; Kitty instances are separate project
  targets, not dynamic Scratch clones.
- A method that returns a number or condition should be called on the sprite
  that owns it.

## Function limits

Custom blocks always run without screen refresh. `warp=True` is ignored.
`kitty.wait(...)` creates pauses even inside a custom block.

Additional function limits:

- `*args` supports at most 8 extra positional values.
- `**kwargs` supports at most 4 extra keyword pairs.
- List and dictionary default values are not supported.
- Positional-only parameters using `/` are not supported.
- A block marked `@kitty.block` cannot return a value.

## Range limits

`range()` accepts one, two, or three numeric arguments. A step of `0` is
rejected. Empty ranges do not create a loop variable.
