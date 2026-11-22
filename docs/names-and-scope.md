## Names and scope

A name you set at the top of a sprite is that sprite's variable. Everyone on that sprite can read it. A name you set inside a function belongs to that call. `points` here is not the sprite's `points`. Another call of `score_points` has its own `points`. If you read it before you set it, it starts at `0`.

```python
def score_points():
    points = 0
    points += 1
```

To change a sprite variable from inside a function, write `global` and the name. The variable has to exist above the function.

```python
score = 0

@kitty.green_flag
def start():
    global score
    score += 1
```

Reading a sprite variable needs no `global` when the function never sets that name. `nonlocal` sets a variable that belongs to the function wrapped around this one. See [A function inside a function](functions.md#a-function-inside-a-function).

Number and text names are separate for each call. A list or dictionary name points at one list or dictionary. `same = a` points both names at that one list, so changing it through either name changes the one list. `a = [9]` points `a` at a new list. The walk-through, including functions and slices, is in [Two names, one list](lists.md#two-names-one-list).
