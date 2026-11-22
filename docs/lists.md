# Lists

A list holds many values in one name. It is like a Scratch list, but Kitty
uses `0` for the first position.

## First list

```python
import kitty

items = ["worm", "fish"]

@kitty.green_flag
def start():
    kitty.say(items[0])  # worm
    kitty.say(items[1])  # fish
    kitty.say(len(items))
```

Scratch uses item `1` for the first value. Kitty code uses item `[0]`.

Lists start at 0, the same way Python lists do. `items[0]` is the first item. `items[-1]` is the last item. `"last"`, `"all"`, and `"random"` are extra indexes on a one-dimensional list. `"all"` belongs on delete.

```python
items = ["worm", "fish"]
items.append(3)
items += [4, 5]
more = [6]
items.extend(more)
items.insert(0, 0)
items.remove(2)
last = items.pop()
first = items.pop(0)
spot = items.index(3)
items[0] = "bait"
items[0] *= 3
items.clear()
```

`append` and `+=` add items. `extend` adds every item from another list. `insert` puts an item at an index. `remove` deletes the first matching item. `pop()` deletes the last item and returns it. `pop(0)` deletes the first item and returns it. `index` returns the first matching position, starting at 0. A missing item returns -1. `clear` deletes every item.

`len(items)` is the length. `"worm" in items` searches the list.

`items = []` or a list of numbers and text declares the list. `kitty.list` is the same declaration when you want a Scratch name, a monitor, or a shared list.

### Two names, one list

A name points at a list. `items = []` builds a new list and points the name at it. `same = a` points `same` at the list `a` already points at. Both names are that one list. `same.append(3)` changes the list, so `a` changes too.

```python
a = [1, 2]
same = a
same.append(3)
kitty.say(a[0])
kitty.say(a[1])
kitty.say(a[2])
a = [9]
kitty.say(same[0])
kitty.say(a[0])
```

After `same.append(3)`, the list is `[1, 2, 3]`. `a[0]` is `1`, `a[1]` is `2`, and `a[2]` is `3`. `same[2]` is `3` too.

`a = [9]` builds a new list and points `a` at it. `same` still points at `[1, 2, 3]`, so `same[0]` is `1`. The new `a[0]` is `9`.

`copy = a[:]` builds a new list and fills it with `a`'s items. `part = a[0:2]` is a new list too.

```python
a = [1, 2, 3]
copy = a[:]
copy.append(7)
```

`copy` is `[1, 2, 3, 7]`. `a` is still `[1, 2, 3]`.

A function input points at the caller's list.

```python
def grow(items):
    items.append(4)

a = [1]
grow(a)
kitty.say(a[0])
kitty.say(a[1])
```

`grow` points `items` at `a`'s list, then appends `4`. `a[0]` is `1` and `a[1]` is `4`.

`return items` hands that same list back to the caller. The caller can keep it and change it. Each time the function runs `items = []`, that call builds its own new list.

```python
def make_list():
    items = []
    items.append(1)
    return items

a = make_list()
b = make_list()
a.append(2)
kitty.say(len(a))
kitty.say(a[1])
kitty.say(len(b))
kitty.say(b[0])
```

`a` and `b` are two lists. `len(a)` is `2`, `a[1]` is `2`, `len(b)` is `1`, and `b[0]` is `1`.

A grid is a list too. `other = grid` points both names at that one grid, the same way `same = a` points both names at one list.

### Grids

A nested list is one grid. Kitty stores the items in a row, then the next row, and every row has the same length. Indexes start at 0 on every axis. A name points at that grid. `other = grid` points `other` at the same grid, so changing a square through either name changes the one grid. `grid = [[0, 0], [0, 0]]` builds a new grid and points `grid` at it. `other` still points at the earlier grid.

```python
grid = [
    [1, 2, 3],
    [4, 5, 6],
]
space = [
    [[1, 2], [3, 4]],
    [[5, 6], [7, 8]],
]

kitty.say(grid[1][2])
kitty.say(grid[row][col])
kitty.say(space[1][0][1])
grid[1][2] = 9
grid[row][col] += 1
space[1, 0, 1] = 0
```

`grid[1][2]` is the third square of row 1. `len(grid)` is the number of rows. `len(grid[0])` is the length of a row. `len(space[0][0])` is the length of the last dimension.

```python
grid = [
    [1, 2],
    [3, 4],
]
other = grid
other[0][1] = 9
kitty.say(grid[0][1])
grid = [[0, 0], [0, 0]]
kitty.say(other[0][1])
kitty.say(grid[0][0])
```

`other[0][1] = 9` changes the grid both names point at, so `grid[0][1]` is `9`. The later `grid = [[0, 0], [0, 0]]` points `grid` at a new grid. `other[0][1]` is still `9`, and the new `grid[0][0]` is `0`.

A function input points at the caller's grid.

```python
def paint(grid):
    grid[0][1] = 8

board = [[1, 2], [3, 4]]
paint(board)
kitty.say(board[0][1])
```

`paint` points its `grid` at `board`, then changes that square. `board[0][1]` is `8`.

`append`, `extend`, `insert`, `remove`, `pop`, `clear`, and the `kitty` list blocks stay on one-dimensional lists. Change a grid square with `grid[row][col] = value`. `value in grid` still searches every square. A new grid written with `[[...], [...]]` keeps one length for every row.
