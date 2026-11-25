## Variables and lists

Declaring `score = 0`, `items = [1, 2]`, or `scores = {"ada": 3}` is enough when the Scratch name can match the Python name. Use these functions for a different Scratch name, a monitor, or a value shared by every sprite. List and dictionary behavior is in [Lists](lists.md#lists) and [Dictionaries](dictionaries.md#dictionaries).

### kitty.variable

Declare a variable. Use this when the name on the stage should differ from the Python name, when the value should appear on the stage, or when every sprite should share it. `score = 0` is enough when none of those matter.

**name:** the name Scratch shows.

**value:** the starting number or text. The default is `0`.

**shared:** `True` puts the variable on the stage so every sprite reads the same one. `False` keeps it on this sprite. The default is `False`.

**show:** `True` puts a monitor on the stage so you can watch the value. `False` hides it. The default is `False`. You can still show it later with `kitty.show_variable`.

```python
score = kitty.variable("Score", 0)
lives = kitty.variable("lives", 9, show=True)
points = kitty.variable("points", 0, shared=True)
```

The Python name and the Scratch name can both be used:

```python
score = kitty.variable("Score", 0)
score += 1
kitty.set(score, 10)
```

### kitty.set

Set a variable. `score = value` is the same block.

**variable:** the variable.

**value:** the new number or text.

```python
score = 0
kitty.set(score, "done")
```

### kitty.change

Change a variable by a number. `score += value` and `score -= value` are the same block.

**variable:** the variable.

**value:** how much to add.

```python
score += 1
score -= 1
```

### kitty.show_variable

Show a variable's monitor.

**variable:** the variable.

```python
kitty.show_variable(score)
```

### kitty.hide_variable

Hide a variable's monitor.

**variable:** the variable.

```python
kitty.hide_variable(score)
```

### kitty.dict

Declare a dictionary. The Scratch lists are named `name keys` and `name values`.

**name:** the Scratch name.

**value:** the starting pairs. The default is an empty dictionary.

**shared:** `True` puts both lists on the stage.

**show:** `True` shows both monitors.

```python
scores = kitty.dict("Scores", {"ada": 3})
empty = kitty.dict("Empty")
board = kitty.dict("Board", {}, shared=True, show=True)
```

`scores = {"ada": 3}` declares the same kind of dictionary when the Scratch name can match the Python name.

### kitty.list

Declare a list.

**name:** the Scratch name.

**value:** the starting items. The default is an empty list.

**shared:** `True` puts it on the stage.

**show:** `True` shows the monitor.

**scratch:** `True` keeps the items in this one Scratch list, changed by Scratch's own list blocks. The default is `False`. `kitty decomp` writes Scratch lists this way. A shared list with `scratch=True` can be declared in every sprite file that uses it, with the same items, and they all use the one list.

```python
items = kitty.list("items", ["worm"])
bag = kitty.list("bag", shared=True, show=True)
log = kitty.list("log", [], scratch=True, shared=True)
```

`items = ["worm"]` declares the same kind of list when the Scratch name can match the Python name. Indexes start at 0. Use `append`, `extend`, `insert`, `remove`, `pop`, `index`, and `clear` on the list.

### kitty.add

Add an item to a one-dimensional list. `items.append(item)` is the same block. This is not number addition.

**item:** the item.

**list:** the list.

```python
items.append("fish")
kitty.add("fish", items)
```

### kitty.delete

Delete an item from a one-dimensional list.

**index:** the position, starting at 0, or `last`, `all`, or `random`.

**list:** the list.

```python
kitty.delete(0, items)
kitty.delete("last", items)
kitty.delete("all", items)
kitty.delete("random", items)
```

### kitty.delete_all

Delete every item in a one-dimensional list. `items.clear()` is the same block.

**list:** the list.

```python
items.clear()
```

### kitty.insert

Insert an item in a one-dimensional list. `items.insert(index, item)` is the same idea. The index starts at 0.

**item:** the item.

**index:** the position, or `last` or `random`.

**list:** the list.

```python
items.insert(0, "fish")
kitty.insert("worm", "last", items)
```

### kitty.replace

Replace an item in a one-dimensional list. `items[index] = item` is the same block.

**index:** the position, starting at 0, or `last` or `random`.

**list:** the list.

**item:** the new item.

```python
items[0] = "bait"
kitty.replace("last", items, "bait")
```

### kitty.item_of

Read an item. `items[index]` is the same block. The first item is 0.

**index:** the position, or `last` or `random`.

**list:** the list.

```python
kitty.say(items[0])
kitty.say(kitty.item_of("last", items))
kitty.say(kitty.item_of("random", items))
```

### kitty.item_number

Where an item first appears, starting at 0. `items.index(item)` is the same idea. A missing item returns -1.

**item:** the item to find.

**list:** the list.

```python
kitty.say(items.index("fish"))
```

### kitty.show_list

Show a list's monitor.

**list:** the list.

```python
kitty.show_list(items)
```

### kitty.hide_list

Hide a list's monitor.

**list:** the list.

```python
kitty.hide_list(items)
```
