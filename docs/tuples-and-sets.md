## Tuples and sets

A tuple is a list you do not change in place. You can read it, unpack it, and assign a new tuple to the name.

```python
point = (3, 4)
x, y = point
x, y = y, x
point = (0, 1)
```

`point[0] = 9` is an error. A set keeps each item once. `{}` is still a dictionary. A set is written with items, or with `set()`.

```python
seen = {1, 2}
seen.add(2)
seen.add(3)
seen.discard(1)
if 3 in seen:
    kitty.say(len(seen))
```

A set also has `remove`, `pop`, and `clear`.
