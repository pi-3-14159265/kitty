# Kitty

Kitty compiles Python into a Scratch 3 project. A script is not run by Python. `comp.py` reads it and writes an `.sb3` file.

Write the Python operation when Python already has one. `score += 1`, `items.append(3)`, and `math.sin(math.pi / 2)` become Scratch blocks. Things Python does not have, such as speech bubbles and sprite properties, are functions on `kitty`.

Menu arguments list their choices in the editor. Type the opening quote of `kitty.property_of("` and pick `x position`, `y position`, `direction`, or another property. The same popup exists for effects, keys, rotation styles, and the other Scratch menus. `self.property_of` shows the same choices.

## Compile

```bash
python comp.py script.py
python comp.py stage.py cat.py -o game.sb3
python comp.py folder/
```

One script becomes `<name>.sb3` next to that file. Several scripts, or a directory, become `project.sb3`. A directory compiles every `.py` file in it except `comp.py`, `kitty.py`, and `decomp.py`.

```bash
python decomp.py game.sb3
python decomp.py game.sb3 output_folder
```

`decomp` writes the project back out as a folder. Each sprite gets a directory, with its script next to its costumes and sounds. The stage is the `Stage` directory. `project.txt` sits at the top.

## Scripts

```python
import kitty

score = 0
kitty.say("Hello world!")
kitty.move(10)
```

`from kitty import say` works too. Call `say("Hello world!")`.

Statements at the top of a file run when the green flag is clicked. A decorated function is another script, and the two run at the same time:

```python
@kitty.green_flag
def start():
    kitty.say("Hello world!")
```

Inside a sprite class, call the same blocks on `self`:

```python
self.say("Hello world!")
self.move(10)
```

## Values and math

A name at the top of a sprite, holding a number, text, list, or dictionary, declares that value. A later assignment compiles to `set`.

```python
score = 0
name = "Ada"
score = score + 1
score += 1
score -= 1
score *= 2
score /= 2
score //= 2
score %= 2
```

`+=` and `-=` are Scratch's change block. `*=`, `/=`, `//=`, and `%=` set the variable to that result. `//` is floor of the division.

`+`, `-`, `*`, `/`, `//`, and `%` are the operator blocks. `+` on text joins text. There is no number block named `kitty.add`. `kitty.add` adds an item to a list.

```python
kitty.say(score // 2)
kitty.say("Hello " + name)
```

Comparisons are `>`, `<`, `>=`, `<=`, `==`, and `!=`. `and`, `or`, and `not` are the boolean blocks.

```python
if score > 10 and kitty.touching("edge"):
    kitty.hide()
```

`import math` and `from math import sin` both work. Sine, cosine, tangent, and their inverses take radians, the same as Python. A full turn is `2 * math.pi` radians, about 6.28, which is the same turn as 360 degrees. A quarter turn is `math.pi / 2`, the same as 90 degrees. `math.pi` and `math.e` are the usual constants. `kitty.sin` stays in degrees, because that is the Scratch block.

```python
import math

kitty.say(math.sin(math.pi / 2))
kitty.say(math.sqrt(9))
kitty.say(math.floor(1.8))
kitty.say(math.ceil(1.2))
kitty.say(math.log(8))
kitty.say(math.log10(100))
kitty.say(math.exp(1))
kitty.say(abs(-3))
kitty.say(round(1.6))
```

| Python | Scratch block |
| --- | --- |
| `math.sin`, `math.cos`, `math.tan` | sin, cos, tan, after converting radians to degrees |
| `math.asin`, `math.acos`, `math.atan` | asin, acos, atan, then converted back to radians |
| `math.floor` | floor |
| `math.ceil` | ceiling |
| `math.sqrt` | sqrt |
| `math.log` | natural log |
| `math.log10` | log base 10 |
| `math.exp` | e raised to a power |
| `math.fabs`, `abs` | abs |
| `round` | round |

`kitty.sin(90)` is sine of 90 degrees. `math.sin(math.pi / 2)` is the same result, measured in radians. `len` reads the length of a list, a dictionary, or text.

## Choices and loops

`if`, `elif`, `else`, `while`, and `for` compile to Scratch control blocks. `with kitty.repeat(...)`, `with kitty.forever()`, `with kitty.if_(...)`, and `with kitty.repeat_until(...)` are those same blocks.

```python
if kitty.touching("mouse-pointer"):
    kitty.say("boop")
elif kitty.key_pressed("space"):
    kitty.move(10)
else:
    kitty.hide()

for i in range(4):
    kitty.say(i)

for i in range(1, 4):
    kitty.move(i)

for i in range(10, 0, -2):
    kitty.say(i)

for _ in range(10):
    kitty.move(10)

while not kitty.key_pressed("space"):
    kitty.move(10)

while True:
    kitty.move(10)
```

`for i in range(n)` creates `i` when that name is not already a variable and the loop runs at least once. The body sees `0`, `1`, and so on, stopping before `n`. After `for i in range(3)`, `i` is `2`. A range that is empty in the code, such as `range(0)` or `range(3, 3)`, does not create `i` and does not change an `i` you already have. `for _ in range(n)` and `for _ in range(0, n)` repeat without a counter. A step of `0` is an error.

```python
for item in items:
    kitty.say(item)

for name in scores:
    kitty.say(scores[name])
```

A list loop sets the name to each item. A dictionary loop sets the name to each key.

`while not condition` is repeat-until that condition. `while condition` is repeat-until the condition is false. `with kitty.if_` has no else. Use a Python `if` when you need `elif` or `else`.

## Lists

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

## Dictionaries

A dictionary is two Scratch lists, one for keys and one for values. Keys and values are numbers or text.

```python
scores = {"ada": 3, "bea": 5}
kitty.say(scores["ada"])
kitty.say(scores[name])
scores["ada"] = 9
scores[name] = 4
scores[name] += 1

if "bea" in scores:
    kitty.say(len(scores))

for name in scores:
    kitty.say(scores[name])

kitty.say(scores.get("nope", 0))
scores.update({"bea": 4})
gone = scores.pop("ada")
scores.clear()
```

`scores["ada"]` reads the value. Assigning a missing key adds it. `get` uses the second value when the key is missing. `update` adds those pairs and keeps the keys that are already there. `pop` reads a value and removes that key. `clear` deletes every key and value. `{}` starts an empty dictionary.

A dictionary name points at one dictionary. `other = scores` points both names at that dictionary.

```python
scores = {"ada": 3}
other = scores
other["ada"] = 9
kitty.say(scores["ada"])
```

`other["ada"] = 9` changes that dictionary, so `scores["ada"]` is `9`.

`scores = {}` points `scores` at a new dictionary. `other` still has the old keys and values.

`kitty.dict` is the same declaration when you want a Scratch name, monitors, or a shared dictionary. The lists are named `name keys` and `name values`.

## Functions

A function is a named chunk of blocks you can run again. Kitty has two kinds.

A **hat** starts by itself when something happens: the green flag, a key, a click, a message. The `@` line above a function is a decorator. It tells Kitty what starts that function, as in `@kitty.green_flag`. A hat starts with no inputs and hands back no answer. Two hats run side by side. A `move` loop on a hat shows each step, because Scratch takes turns between scripts.

A **custom block** runs when you call it, the way `greet("hi")` runs `greet`. The names in the parentheses are the block's inputs. In Scratch they are the blanks on the block. `@kitty.block` is this kind of function. The functions that hand back an answer are `@kitty.number` and `@kitty.boolean`.

```python
def greet(name):
    kitty.say(name)

greet("hi")
```

`@kitty.block` means the same thing. Write it when you want the kind of function to be obvious. `@kitty.block` cannot `return`.

```python
@kitty.block
def greet(name, loud=False):
    kitty.say(name)
    if loud:
        kitty.think("!!")

greet("hi", True)
```

### Answers

Scratch cannot hand a custom block's answer straight back to the caller. Kitty runs the block, saves the answer, and the caller reads that saved answer.

Use `return` to set the answer. A function that returns a number or text is a number function. You can write `@kitty.number`, or leave the decorator off: a `return` of a number or text is enough.

```python
@kitty.number
def double(n):
    return n * 2

@kitty.number
def clamp(n):
    if n < 0:
        return 0
    if n > 10:
        return 10
    return n

kitty.say(double(1) + double(2))
kitty.say(double(double(3)))
```

Every number function needs a `return` somewhere. A path that never reaches one leaves the answer at `0`. In `clamp`, a negative `n` returns `0` and skips the rest. A huge `n` returns `10`. Anything else returns `n`.

`@kitty.boolean` returns a true-or-false test you can put in `if`. Kitty stores true as `1` and false as `0`. A `return` that is a comparison, `and`, `or`, `not`, `True`, or `False` is a boolean function even without the decorator. If you are not sure which kind you made, write `@kitty.boolean` or `@kitty.number`.

```python
@kitty.boolean
def big(n):
    return n > 10

@kitty.boolean
def blocked():
    return kitty.touching("edge") or kitty.touching("Cat")

if big(score):
    kitty.say("big")

if not blocked():
    kitty.move(10)
```

`return a, b` hands back more than one answer. The caller splits them into names, as in `left, right = pair(3)`. Every `return` in that function has to hand back the same number of answers.

```python
@kitty.number
def pair(n):
    return n, n + 1

left, right = pair(3)
kitty.say(left)
kitty.say(right)
```

`pair(3)` sets `left` to `3` and `right` to `4`.

### Calling itself

A function can call itself. Each call keeps its own inputs and its own number and text variables, so the inner call does not erase the outer one.

```python
@kitty.number
def factorial(n):
    if n < 2:
        return 1
    return n * factorial(n - 1)
```

`factorial(3)` calls `factorial(2)`, which calls `factorial(1)`. The inner call returns `1`. Then `factorial(2)` returns `2 * 1`, and `factorial(3)` returns `3 * 2`. The answer is `6`.

### What you see in Scratch

The block you call looks like the Python function: `greet (name) (loud)`. Kitty also builds a second block, `greet run`, and calls that one for you. You keep calling `greet`.

Each call gets its own number and text variables. Scratch shows them as lists. `greet name` has one row per call. That is why two scripts can call `greet` at the same time and each one still has its own `name`.

Each run of `items = []` or `scores = {}` builds a new list or dictionary for that call. A call to itself gets its own. `return items` hands that same list back, and the caller keeps it. Two names can also point at one list. See [Two names, one list](#two-names-one-list).

### Screen refresh

Scratch normally runs one block, draws the screen, then lets the next script take a turn. A custom block keeps going until it finishes or reaches `kitty.wait`, and the screen draws after that. Scratch calls this "run without screen refresh."

That is what keeps each call's variables separate. It also changes how motion looks:

```python
def dash():
    for _ in range(10):
        kitty.move(10)

def walk():
    for _ in range(10):
        kitty.move(10)
        kitty.wait(0.1)
```

`dash()` finishes all 10 moves before the screen draws, so the sprite appears at the end. `walk()` pauses on every step, so you see the walk. A hat script, such as `@kitty.green_flag`, still takes turns with other scripts. A `move` loop there animates even without `wait`.

`warp=True` and `warp=False` do not change this. Custom blocks always run without screen refresh. `kitty.wait` still waits.

### Defaults

A default is the value Kitty uses when the caller leaves that input out. It can be a number, text, `True`, or `False`. Writing `loud=False` or `loud: bool` makes a true-or-false input, the hexagonal one in Scratch. The other inputs are numbers or text. A list or a dictionary cannot be a default.

```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

That default is unsupported. Python builds the `[]` once and reuses that same list on every call that leaves `items` out. Write `items = []` inside the function. Each call builds its own list.

```python
def greet(name="ada", times=2):
    for _ in range(times):
        kitty.say(name)

greet()
greet("bea")
greet("bea", 1)
greet(times=1)
```

`greet()` says `ada` twice. `greet("bea")` says `bea` twice. `greet("bea", 1)` says it once. `greet(times=1)` says `ada` once, because `name` still has its default.

### Extra inputs

`*args` collects extra values that do not have their own name. You can pass up to 8 of them. `args[0]` is the first extra value. `len(args)` is how many were passed. `for item in args` visits each one.

```python
@kitty.number
def total(first, *args):
    result = first
    for item in args:
        result += item
    return result

kitty.say(total(1, 2, 3))
```

`total(1, 2, 3)` starts at `1`, then adds `2` and `3`. The answer is `6`. In Scratch the block has `first`, then `arg count`, then `arg 1` through `arg 8`. Kitty fills those. You still call it as `total(1, 2, 3)`.

`**kwargs` collects extra named inputs, up to 4. Read one with `kwargs["note"]`. `len(kwargs)` is how many were passed. `for name in kwargs` visits the names.

```python
def show_extra(n=1, **kwargs):
    kitty.say(kwargs["note"])
    kitty.say(n)

show_extra(note="hi")
show_extra(4, note="hi")
```

The Scratch block shows `keyword count`, then `key 1`, `value 1`, and so on up to 4 pairs. A missing key reads as empty text.

An input written after `*args` has to be passed by name:

```python
def greet(name, *args, loud=False):
    kitty.say(name)

greet("hi", 1, 2, loud=True)
```

### A function inside a function

The inner function can read the outer function's variables. Its Scratch name includes the outer name, so `inner` inside `outer` is the block `outer inner`.

```python
@kitty.number
def outer(n):
    def inner(x):
        return x + n
    return inner(n)
```

`outer(5)` calls `inner(5)`. `inner` reads `n`, which is `5`, and returns `10`.

`nonlocal` means "change the outer function's variable, not a new one."

```python
@kitty.number
def remember(n):
    def inner(x):
        nonlocal n
        n = n + x
        return n
    return inner(1)
```

`remember(4)` calls `inner(1)`. `inner` changes the outer `n` from `4` to `5` and returns `5`.

### On a sprite

The first input of a method is `self`. Scratch does not show it. Call the method on the sprite: `self.score_plus(3)`.

```python
class Cat(kitty.Sprite):
    def __init__(self):
        self.hp = 4

    @kitty.number
    def score_plus(self, n):
        return self.hp + n

    @kitty.green_flag
    def start(self):
        self.say(self.score_plus(3))
```

`self.hp` is the sprite's variable. `n` belongs to that call. The answer is `7`.

Call a number or boolean method on the sprite that defines it. `mouse.score_plus(3)` does not work, because the saved answer stays on the mouse. A method that does not return can be called on another sprite. That sends a message and waits. See [Sprites](#sprites).

### Lambda

A lambda is a one-line function. It is still a custom block. A comparison makes it a condition. It can call another lambda, and it can call itself.

```python
double = lambda n: n * 2
big = lambda n: n > 3

kitty.say(double(4))
kitty.say((lambda n: n + 1)(10))

if big(score):
    kitty.say("big")
```

`(lambda n: n + 1)(10)` builds the block and calls it once. The answer is `11`.

On a class, leave `self` off the lambda. The block's inputs are the lambda's arguments.

```python
class Cat(kitty.Sprite):
    def __init__(self):
        self.hp = 4

    hit = lambda n: self.hp - n

    @kitty.green_flag
    def start(self):
        self.say(self.hit(1))
```

## Sprites

Each file is one sprite, named after the file. A file named `stage.py` is the stage. A project can have only one stage.

A class that inherits `kitty.Sprite` is a sprite. A class that inherits `kitty.Stage` is the stage. `self.hp = 9` is a variable on that sprite. A method is a custom block, unless it has a hat decorator. The first parameter must be named `self`, and it is left off the Scratch block. Hat methods cannot take more parameters.

```python
import kitty

class Animal(kitty.Sprite):
    title = "pet"

    def __init__(self):
        self.hp = 1

    def speak(self):
        self.say(self.title)

class Cat(Animal):
    def __init__(self, lives):
        super().__init__()
        self.hp = lives
        self.say("born")

    def speak(self):
        super().speak()
        self.say("meow")

    @kitty.green_flag
    def start(self):
        self.speak()
        self.move(10)

felix = Cat(9)
mittens = Cat(3)
```

`felix = Cat(9)` and `mittens = Cat(3)` are two sprites. `hp` starts at the value passed in. `title` starts as `"pet"`. `speak` is a custom block. `start` runs when the green flag is clicked, and `say "born"` from `__init__` is placed at the front of that script. Constructor arguments must be numbers, text, or lists, because each instance is baked into the project. Scratch clones share one sprite, so Kitty does not turn instances into clones.

If you never write `felix = Cat()`, the class itself becomes one sprite named `Cat`. A class that only exists so other classes can inherit it does not become its own sprite.

```python
class Game(kitty.Stage):
    @kitty.green_flag
    def start(self):
        self.switch_backdrop("backdrop1")
```

`super().speak()` compiles the parent method under its own name, `Animal speak`, and calls that block.

A call on another sprite waits for that sprite to run the method:

```python
class Mouse(kitty.Sprite):
    def squeak(self, word):
        self.say(word)

class Cat(kitty.Sprite):
    @kitty.green_flag
    def start(self):
        mouse.squeak("hi")
        self.say(mouse.x_position())

mouse = Mouse()
```

`mouse.squeak("hi")` copies each number or piece of text into a shared variable, sends the mouse a message, and waits until that script finishes. A variable that holds a number or text is copied the same way. A `True` or `False` input is refused. A list arrives as one piece of text, the items stuck together, so pass a number or text when the other sprite needs the value itself. A method that returns a number or a condition stays on the sprite that defines it, so call that method with `self`.

`mouse.x_position()` reads `x position of mouse`. The same readers are `y_position`, `direction`, `size`, `costume_number`, `costume_name`, and `volume`.

Another sprite's variables stay on that sprite. Share a variable by declaring it with `shared=True`:

```python
score = kitty.variable("score", 0, shared=True)

class Cat(kitty.Sprite):
    @kitty.green_flag
    def start(self):
        global score
        score += 1
```

Every block function is also a method, so `self.say("hi")` is `kitty.say("hi")`. `self.clone()` creates a clone of this sprite. Declarations, hat decorators, `kitty.length`, `kitty.contains`, and `kitty.math` stay on `kitty`.

A sprite with no costume gets a blue circle. A stage with no backdrop gets a white backdrop named `backdrop1`.

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

Reading a sprite variable needs no `global` when the function never sets that name. `nonlocal` sets a variable that belongs to the function wrapped around this one. See [A function inside a function](#a-function-inside-a-function).

Number and text names are separate for each call. A list or dictionary name points at one list or dictionary. `same = a` points both names at that one list, so changing it through either name changes the one list. `a = [9]` points `a` at a new list. The walk-through, including functions and slices, is in [Two names, one list](#two-names-one-list).

## break and continue

`break` leaves the loop. `continue` skips the rest of this pass and goes on to the next one. A `for` loop still steps forward after `continue`.

```python
for i in range(10):
    if i == 2:
        continue
    if i == 5:
        break
    kitty.say(i)
```

## try and except

`try` / `except` catches `raise` only. Scratch does not turn its own problems into exceptions. A bad index, a missing dictionary key, division by zero, and an unknown name do not jump into `except`. Write `raise` when you want the `except` block to run. `except` and `except Exception` both catch that `raise`. `except Exception as problem` stores the message in `problem`. `else` runs when nothing was raised. `finally` always runs.

```python
try:
    raise Exception("missing")
except Exception as problem:
    kitty.say(problem)
else:
    kitty.say("ok")
finally:
    kitty.say("done")
```

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

## Text

Read text the way Python reads it. `text[0]` is the first letter. `text[1:4]` is a slice. `kitty.letter` is the Scratch block, and that block still starts at 1.

```python
word = "Hello"
kitty.say(word[0])
kitty.say(word[1:4])
kitty.say(word.upper())
kitty.say("  hi ".strip())
kitty.say("a-b".split("-")[0])
kitty.say("-".join(["a", "b"]))
kitty.say("cater".replace("cat", "dog"))
kitty.say("cater".find("at"))
kitty.say("banana".count("a"))
kitty.say(word.startswith("He"))
kitty.say(word.endswith("o"))
kitty.say("12".isdigit())
kitty.say("ab".isalpha())
kitty.say(f"n={score}")
```

`lower`, `lstrip`, and `rstrip` are there too. `strip` removes spaces. `find` returns -1 when the text is missing. An f-string joins the pieces. A format spec such as `f"{n:.2f}"` is not supported.

## Slices, comprehensions, enumerate, and zip

A slice builds a new list. The new list has its own items, so changing the slice leaves the original list as it was. The step is a whole number.

```python
part = items[0:2]
copy = items[:]
back = items[::-1]
```

A comprehension has one `for` and any number of `if` tests.

```python
doubled = [n * 2 for n in counts if n != 2]
```

`enumerate` counts from 0. `zip` stops at the shorter list.

```python
for i, item in enumerate(items):
    kitty.say(i)
    kitty.say(item)

for a, b in zip(items, counts):
    kitty.say(a)
    kitty.say(b)
```

# Reference

Each entry is the function the editor completes. The argument list is the popup. Where a menu has fixed choices, those choices are the ones the popup offers.

## Events

A hat starts a script when something happens. It sits on a function or on a method. A function keeps one hat. Hats do not take inputs. Custom blocks, which you call yourself, are [Functions](#functions).

### kitty.green_flag

Run this function when the green flag is clicked. Top-level statements are already one green-flag script, so this is a second one. The two run at the same time.

```python
@kitty.green_flag
def start():
    kitty.say("Hello world!")
```

### kitty.when_key

Run this function when a key is pressed.

**key:** `space`, `up arrow`, `down arrow`, `left arrow`, `right arrow`, `enter`, `any`, or a letter or digit. `up`, `down`, `left`, and `right` are the arrow keys.

```python
@kitty.when_key("space")
def hop():
    kitty.move(10)

@kitty.when_key("up")
def climb():
    kitty.change_y(10)
```

### kitty.when_clicked

Run this function when this sprite is clicked. On the stage, this is when the stage is clicked.

```python
@kitty.when_clicked
def poked():
    kitty.say("hey")
```

### kitty.when_stage_clicked

Run this function when the stage is clicked.

```python
@kitty.when_stage_clicked
def poked():
    kitty.switch_backdrop("backdrop1")
```

### kitty.when_backdrop

Run this function when the backdrop switches to a name.

**name:** the backdrop's name.

```python
@kitty.when_backdrop("beach")
def arrive():
    kitty.say("sand")
```

### kitty.when_loudness

Run this function when the loudness is greater than a number.

**value:** the loudness to pass.

```python
@kitty.when_loudness(10)
def heard():
    kitty.say("loud")
```

### kitty.when_timer

Run this function when the timer is greater than a number of seconds.

**value:** seconds on the timer.

```python
@kitty.when_timer(5)
def later():
    kitty.say("time")
```

### kitty.when_receive

Run this function when a message is broadcast. Send it with `kitty.broadcast` or `kitty.broadcast_and_wait`.

**message:** the message name.

```python
@kitty.when_receive("go")
def go():
    kitty.move(10)
```

### kitty.when_cloned

Run this function when this sprite starts as a clone.

```python
@kitty.when_cloned
def born():
    kitty.say("clone")
```

### kitty.block

Define a custom block that you call by name. It does not return an answer. A `def` with no decorator and no `return` is the same kind of block. A default of `True` or `False`, or a `bool` note, makes a boolean input. Other defaults are numbers or text. A list or a dictionary cannot be a default. See [Defaults](#defaults).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `warp=True` and `warp=False` do not change that. See [Screen refresh](#screen-refresh).

```python
@kitty.block
def greet(name, loud=False):
    kitty.say(name)
```

### kitty.number

Define a custom block that returns a number or text. The body uses `return`. A `def` that returns a number or text is the same kind of block, even without this decorator. See [Answers](#answers).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `warp` does not change that.

```python
@kitty.number
def double(n):
    return n * 2
```

### kitty.boolean

Define a custom block that returns true or false. Use it in `if`. The body uses `return` with a comparison, `and`, `or`, `not`, `True`, or `False`. See [Answers](#answers).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `warp` does not change that.

```python
@kitty.boolean
def big(n):
    return n > 10
```

### kitty.sprite

Put the decorated function on its own sprite. The function body is that sprite's top level: declarations, hats, and custom blocks.

**name:** the sprite's name. Omit it to use the function name.

```python
@kitty.sprite("Cat")
def cat():
    kitty.say("meow")

@kitty.sprite
def mouse():
    kitty.say("squeak")
```

### kitty.stage

Put the decorated function on the stage. A project can have only one stage. A file named `stage.py` is the stage too.

```python
@kitty.stage
def backdrop():
    kitty.switch_backdrop("backdrop1")
```

### kitty.Sprite

A class that inherits `kitty.Sprite` is a sprite. See [Sprites](#sprites).

### kitty.Stage

A class that inherits `kitty.Stage` is the stage. Backdrop declarations belong here. See [Sprites](#sprites).

## Motion

Menu targets accept a sprite name. `mouse` is the same as `mouse-pointer`.

### The Scratch screen and SVG coordinates

Scratch uses **screen coordinates**, not HTML/SVG page coordinates:

- the actual center of the screen is `(0, 0)`
- x increases to the right, from `-240` to `240`
- y increases upward, from `-180` to `180`
- the top-left of the stage is approximately `(-240, 180)`
- the bottom-right of the stage is approximately `(240, -180)`

Consequently, `kitty.go_to_xy(0, 0)` places a sprite at the center of the
screen. It does not place the sprite at the top-left or in the corner.

SVG artwork is also easier to use if its visible subject is centered in the
SVG canvas. The image itself does not use Scratch coordinates: a 64 x 64
costume is not drawn with `(0, 0)` at its top-left in Scratch. A full stage
backdrop is commonly 480 x 360, with its pixel center at `(240, 180)` inside
the SVG. Scratch maps that center to screen coordinate `(0, 0)`.

For example, this costume is intentionally centered around SVG point
`(32, 32)`:

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="24" fill="#4C97FF"/>
</svg>
```

This is more reliable than drawing the subject in a corner and using an
offset in Python. If the subject is a 64 x 64 circle whose center is
`(32, 32)`, placing the sprite at `(0, 0)` puts the circle at the center of
the screen.

For a 480 x 360 backdrop, keep the scene centered around `(240, 180)`:

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     width="480" height="360" viewBox="0 0 480 360">
  <rect width="480" height="360" fill="#78B84A"/>
  <circle cx="240" cy="180" r="30" fill="#FFFFFF"/>
</svg>
```

Do not convert SVG coordinates directly into Kitty coordinates. An SVG point
such as `(240, 180)` is a pixel position in the image; Scratch screen
coordinate `(0, 0)` is the stage center. Kitty movement functions such as
`kitty.go_to_xy(0, 0)` and `self.go_to_xy(0, 0)` always use Scratch screen
coordinates.

### kitty.move

Move the sprite.

**steps:** how many steps to move.

```python
kitty.move(10)
kitty.move(score)
```

### kitty.turn_right

Turn right.

**degrees:** how far to turn.

```python
kitty.turn_right(15)
```

### kitty.turn_left

Turn left.

**degrees:** how far to turn.

```python
kitty.turn_left(15)
```

### kitty.go_to

Go straight to a target.

**target:** `mouse-pointer`, `random position`, or a sprite name.

```python
kitty.go_to("mouse-pointer")
kitty.go_to("random position")
kitty.go_to("Cat")
```

### kitty.go_to_xy

Go to an x and y position.

**x:** the x position.

**y:** the y position.

```python
kitty.go_to_xy(0, 0)
kitty.go_to_xy(kitty.mouse_x(), kitty.mouse_y())
```

### kitty.glide_to

Glide to a target.

**seconds:** how long the glide takes.

**target:** `mouse-pointer`, `random position`, or a sprite name.

```python
kitty.glide_to(1, "mouse-pointer")
kitty.glide_to(0.5, "random position")
```

### kitty.glide_to_xy

Glide to an x and y position.

**seconds:** how long the glide takes.

**x:** the x position.

**y:** the y position.

```python
kitty.glide_to_xy(1, 0, 0)
```

### kitty.point_in_direction

Point in a direction. `90` is right, `0` is up, `-90` is left, and `180` is down. These degrees are the sprite's direction. They are separate from `math.sin`, which uses radians.

**direction:** degrees.

```python
kitty.point_in_direction(90)
```

### kitty.point_towards

Point towards a target. There is no random position on this block.

**target:** `mouse-pointer`, or a sprite name.

```python
kitty.point_towards("mouse-pointer")
kitty.point_towards("Cat")
```

### kitty.change_x

Change x.

**dx:** how much to add.

```python
kitty.change_x(10)
```

### kitty.set_x

Set x.

**x:** the new position.

```python
kitty.set_x(0)
```

### kitty.change_y

Change y.

**dy:** how much to add.

```python
kitty.change_y(10)
```

### kitty.set_y

Set y.

**y:** the new position.

```python
kitty.set_y(0)
```

### kitty.if_on_edge_bounce

If the sprite is on the edge, bounce.

```python
kitty.if_on_edge_bounce()
```

### kitty.set_rotation_style

Choose what the costume does when the sprite turns. `all around` spins the costume to match the direction, so it can end up upside down. `left-right` flips between facing left and facing right, which fits a side-view character. `don't rotate` leaves the costume upright while the direction still changes. `point_towards` and `move` still use that direction.

**style:** `left-right`, `all around`, or `don't rotate`.

```python
kitty.set_rotation_style("left-right")
kitty.set_rotation_style("all around")
kitty.set_rotation_style("don't rotate")
```

### kitty.x_position

The sprite's x position. On another sprite, `mouse.x_position()` is `x position of mouse`.

```python
kitty.say(kitty.x_position())
```

### kitty.y_position

The sprite's y position.

```python
kitty.say(kitty.y_position())
```

### kitty.direction

The sprite's direction.

```python
kitty.say(kitty.direction())
```

## Looks

### kitty.say

Say a message.

**message:** text or a number.

```python
kitty.say("Hello world!")
kitty.say(score)
```

### kitty.say_for

Say a message, then clear it.

**message:** text or a number.

**seconds:** how long the bubble stays.

```python
kitty.say_for("hi", 2)
```

### kitty.think

Think a message.

**message:** text or a number.

```python
kitty.think("hmm")
```

### kitty.think_for

Think a message, then clear it.

**message:** text or a number.

**seconds:** how long the bubble stays.

```python
kitty.think_for("hmm", 2)
```

### kitty.switch_costume

Switch to a costume on this sprite.

**costume:** the costume's name.

```python
kitty.switch_costume("sitting")
```

### kitty.next_costume

Switch to the next costume.

```python
kitty.next_costume()
```

### kitty.switch_backdrop

Switch the stage's backdrop.

**backdrop:** the backdrop's name.

```python
kitty.switch_backdrop("beach")
```

### kitty.switch_backdrop_and_wait

Switch the backdrop and wait for scripts that start because of that switch.

**backdrop:** the backdrop's name.

```python
kitty.switch_backdrop_and_wait("beach")
```

### kitty.next_backdrop

Switch to the next backdrop.

```python
kitty.next_backdrop()
```

### kitty.change_size

Change the size percent.

**change:** how much to add.

```python
kitty.change_size(10)
```

### kitty.set_size

Set the size percent. `100` is normal size.

**size:** the percent.

```python
kitty.set_size(50)
```

### kitty.change_effect

Change a graphic effect. `color` shifts the costume's colors. `fisheye` bulges the middle. `whirl` twists it. `pixelate` makes it blocky. `mosaic` repeats it in a grid. `brightness` makes it lighter or darker. `ghost` makes it see-through: `0` is solid and `100` is invisible.

**effect:** `color`, `fisheye`, `whirl`, `pixelate`, `mosaic`, `brightness`, or `ghost`.

**change:** how much to add.

```python
kitty.change_effect("color", 25)
kitty.change_effect("ghost", 10)
```

### kitty.set_effect

Set a graphic effect to an amount. The effect names are the same as `change_effect`. `ghost` at `100` hides the sprite while it can still touch things. `hide` removes it from the stage.

**effect:** `color`, `fisheye`, `whirl`, `pixelate`, `mosaic`, `brightness`, or `ghost`.

**value:** the new amount.

```python
kitty.set_effect("ghost", 50)
```

### kitty.clear_graphic_effects

Clear every graphic effect.

```python
kitty.clear_graphic_effects()
```

### kitty.show

Show the sprite.

```python
kitty.show()
```

### kitty.hide

Hide the sprite.

```python
kitty.hide()
```

### kitty.go_to_layer

Move this sprite in front of the others, or behind them. `front` draws it on top. `back` draws it underneath.

**layer:** `front` or `back`.

```python
kitty.go_to_layer("front")
kitty.go_to_layer("back")
```

### kitty.go_layers

Step this sprite forward or backward through the pile of sprites. `forward` moves it toward the front by `number` places. `backward` moves it toward the back.

**direction:** `forward` or `backward`.

**number:** how many layers.

```python
kitty.go_layers("forward", 1)
kitty.go_layers("backward", 2)
```

### kitty.costume_number

The costume's number.

```python
kitty.say(kitty.costume_number())
```

### kitty.costume_name

The costume's name.

```python
kitty.say(kitty.costume_name())
```

### kitty.backdrop_number

The backdrop's number.

```python
kitty.say(kitty.backdrop_number())
```

### kitty.backdrop_name

The backdrop's name.

```python
kitty.say(kitty.backdrop_name())
```

### kitty.size

The size percent.

```python
kitty.say(kitty.size())
```

## Sound

### kitty.play_until_done

Play a sound and wait until it finishes.

**sound:** the sound's name.

```python
kitty.play_until_done("meow")
```

### kitty.start_sound

Start a sound and keep going.

**sound:** the sound's name.

```python
kitty.start_sound("meow")
```

### kitty.stop_all_sounds

Stop every sound.

```python
kitty.stop_all_sounds()
```

### kitty.change_sound_effect

Change a sound effect.

**effect:** `pitch` or `pan left/right`.

**value:** how much to add.

```python
kitty.change_sound_effect("pitch", 10)
```

### kitty.set_sound_effect

Set a sound effect.

**effect:** `pitch` or `pan left/right`.

**value:** the new amount.

```python
kitty.set_sound_effect("pan left/right", 0)
```

### kitty.clear_sound_effects

Clear every sound effect.

```python
kitty.clear_sound_effects()
```

### kitty.change_volume

Change the volume.

**amount:** how much to add.

```python
kitty.change_volume(-10)
```

### kitty.set_volume

Set the volume. `100` is full.

**percent:** the volume.

```python
kitty.set_volume(50)
```

### kitty.volume

The volume.

```python
kitty.say(kitty.volume())
```

## Control

### kitty.wait

Pause this script. Other scripts can run during the pause. Inside a custom block, this is also what lets the screen draw between steps. See [Screen refresh](#screen-refresh).

**seconds:** how long to wait.

```python
kitty.wait(1)
kitty.wait(0.1)
```

### kitty.repeat

Repeat a `with` block. `for _ in range(n)` is the same block. `for i in range(...)` also sets `i`. See [Choices and loops](#choices-and-loops).

**times:** how many times.

```python
with kitty.repeat(10):
    kitty.move(10)
```

### kitty.forever

Repeat a `with` block forever. `while True` is the same block.

```python
with kitty.forever():
    kitty.move(10)
```

### kitty.if_

Run a `with` block when a condition is true. This block has no else. A Python `if` can have `elif` and `else`.

**condition:** a comparison, `touching`, or another boolean.

```python
with kitty.if_(kitty.touching("edge")):
    kitty.hide()
```

### kitty.repeat_until

Repeat a `with` block until a condition is true. `while not condition` is the same block.

**condition:** a comparison, `touching`, or another boolean.

```python
with kitty.repeat_until(kitty.key_pressed("space")):
    kitty.move(10)
```

### kitty.wait_until

Pause until a condition is true. Other scripts keep running while this one waits. `kitty.wait` pauses for a number of seconds. This block pauses until the condition happens.

**condition:** a comparison, `touching`, or another boolean.

```python
kitty.wait_until(kitty.key_pressed("space"))
```

### kitty.stop

Stop scripts. Pick one of the three choices.

**what:** `all` stops every script in the project. `this script` stops the script that reached this block. `other scripts` stops the rest and lets this one continue.

```python
kitty.stop("all")
kitty.stop("this script")
kitty.stop("other scripts")
```

### kitty.create_clone

Make a copy of a sprite. The copy runs the `@kitty.when_cloned` script. The original keeps running. `myself` copies this sprite. A sprite name copies that sprite.

**target:** `myself`, or a sprite name. The default is `myself`.

```python
kitty.create_clone()
kitty.create_clone("Cat")
```

On a sprite class, `self.clone()` creates a clone of that sprite.

### kitty.delete_clone

Remove this clone. The original sprite stays. On the original, this block does nothing.

```python
kitty.delete_clone()
```

## Sensing

Colors are `"#rrggbb"`, six hex digits. The first pair is red, the next is green, and the last is blue. `00` is none and `ff` is full, so `"#ff0000"` is red, `"#00ff00"` is green, and `"#0000ff"` is blue.

### kitty.touching

True when the sprite is touching a target.

**target:** `mouse-pointer`, `edge`, or a sprite name.

```python
if kitty.touching("mouse-pointer"):
    kitty.say("boop")

if kitty.touching("edge"):
    kitty.if_on_edge_bounce()
```

### kitty.touching_color

True when the sprite is touching a color.

**color:** `"#rrggbb"`.

```python
if kitty.touching_color("#ff0000"):
    kitty.say("red")
```

### kitty.color_is_touching

True when a color on this sprite is touching another color.

**color:** the color on this sprite, `"#rrggbb"`.

**color2:** the other color, `"#rrggbb"`.

```python
if kitty.color_is_touching("#ff0000", "#00ff00"):
    kitty.hide()
```

### kitty.distance_to

The distance to a target.

**target:** `mouse-pointer`, or a sprite name.

```python
kitty.say(kitty.distance_to("mouse-pointer"))
```

### kitty.ask

Ask a question and wait. Read the reply with `kitty.answer`.

**question:** the question.

```python
kitty.ask("Your name?")
kitty.say(kitty.answer())
```

### kitty.answer

The text from the last `ask`.

```python
kitty.say(kitty.answer())
```

### kitty.key_pressed

True while a key is down.

**key:** `space`, `up arrow`, `down arrow`, `left arrow`, `right arrow`, `enter`, `any`, or a letter or digit. `up`, `down`, `left`, and `right` are the arrow keys.

```python
if kitty.key_pressed("space"):
    kitty.move(10)
```

### kitty.mouse_down

True while the mouse button is down.

```python
if kitty.mouse_down():
    kitty.say("click")
```

### kitty.mouse_x

The mouse x position.

```python
kitty.say(kitty.mouse_x())
```

### kitty.mouse_y

The mouse y position.

```python
kitty.say(kitty.mouse_y())
```

### kitty.set_drag_mode

Choose whether the viewer can drag this sprite.

**mode:** `draggable` or `not draggable`.

```python
kitty.set_drag_mode("draggable")
```

### kitty.loudness

How loud the microphone is.

```python
kitty.say(kitty.loudness())
```

### kitty.timer

Seconds since the timer was reset.

```python
kitty.say(kitty.timer())
```

### kitty.reset_timer

Set the timer back to 0.

```python
kitty.reset_timer()
```

### kitty.property_of

Read a property of a sprite or the stage.

**property:** `x position`, `y position`, `direction`, `costume #`, `costume name`, `size`, `volume`, `backdrop #`, or `backdrop name`.

**target:** a sprite name, or `stage`.

```python
kitty.say(kitty.property_of("x position", "Cat"))
kitty.say(kitty.property_of("costume name", "Cat"))
kitty.say(kitty.property_of("backdrop name", "stage"))
```

`x` and `y` also mean the positions. `costume number` and `backdrop number` mean `costume #` and `backdrop #`.

### kitty.current

The time on the computer running the project.

**unit:** `year`, `month`, `date`, `day of week`, `hour`, `minute`, or `second`.

```python
kitty.say(kitty.current("hour"))
kitty.say(kitty.current("day of week"))
```

### kitty.days_since_2000

Days since the year 2000.

```python
kitty.say(kitty.days_since_2000())
```

### kitty.username

The viewer's Scratch username.

```python
kitty.say(kitty.username())
```

## Operators

Python writes these as `+`, `-`, `*`, `/`, `//`, `%`, comparisons, `and`, `or`, and `not`. The functions are the same blocks. Number addition is `a + b`, not `kitty.add`.

### kitty.subtract

`a - b`.

**a:** the number to subtract from.

**b:** the number to subtract.

```python
kitty.say(score - 1)
kitty.say(kitty.subtract(score, 1))
```

### kitty.multiply

`a * b`.

```python
kitty.say(score * 2)
```

### kitty.divide

`a / b`.

```python
kitty.say(score / 2)
```

### kitty.mod

The remainder of `a` divided by `b`. `score % 2` is the same block.

```python
kitty.say(score % 2)
```

### kitty.random

A random number from `start` through `end`.

**start:** the low end.

**end:** the high end.

```python
kitty.say(kitty.random(1, 10))
```

### kitty.greater

`a > b`.

```python
if score > 10:
    kitty.say("big")
```

### kitty.less

`a < b`.

```python
if score < 0:
    kitty.say("low")
```

### kitty.equal

`a == b`.

```python
if name == "Ada":
    kitty.say("hi")
```

### kitty.both

`a and b`.

```python
if score > 0 and kitty.touching("edge"):
    kitty.hide()
```

### kitty.either

`a or b`.

```python
if kitty.key_pressed("space") or kitty.mouse_down():
    kitty.say("go")
```

### kitty.not_

`not value`.

```python
if not kitty.key_pressed("space"):
    kitty.move(10)
```

### kitty.join

Join two values into text. `"Hello " + name` is the same block.

**a:** the first value.

**b:** the second value.

```python
kitty.say("Hello " + name)
```

### kitty.letter

One letter of a text. This is the Scratch block, so the first letter is 1. In Python form, `text[0]` is the first letter.

**index:** which letter.

**text:** the text.

```python
kitty.say(kitty.letter(1, "cat"))
```

### kitty.round

Round to the nearest whole number. `round(n)` is the same block.

**n:** the number.

```python
kitty.say(round(1.6))
```

### kitty.abs

The absolute value. `abs(n)` and `math.fabs(n)` are the same block.

**n:** the number.

```python
kitty.say(abs(-3))
```

### kitty.floor

Round down. `math.floor(n)` is the same block.

**n:** the number.

```python
kitty.say(math.floor(1.8))
```

### kitty.ceiling

Round up. `math.ceil(n)` is the same block.

**n:** the number.

```python
kitty.say(math.ceil(1.2))
```

### kitty.sqrt

The square root. `math.sqrt(n)` is the same block.

**n:** the number.

```python
kitty.say(math.sqrt(9))
```

### kitty.sin

Sine of an angle in degrees. This is the Scratch block. `math.sin` uses radians, so `math.sin(math.pi / 2)` matches `kitty.sin(90)`.

**n:** the angle in degrees.

```python
kitty.say(kitty.sin(90))
kitty.say(math.sin(math.pi / 2))
```

### kitty.cos

Cosine of an angle in degrees. `math.cos` uses radians. `math.cos(0)` matches `kitty.cos(0)`, because 0 is the same in both units.

```python
kitty.say(kitty.cos(0))
```

### kitty.tan

Tangent of an angle in degrees. `math.tan` uses radians.

```python
kitty.say(kitty.tan(45))
```

### kitty.asin

Arcsine in degrees. The Scratch block reads a sine and answers with degrees. `math.asin` answers in radians.

```python
kitty.say(kitty.asin(1))
```

### kitty.acos

Arccosine in degrees. `math.acos` answers in radians.

```python
kitty.say(kitty.acos(1))
```

### kitty.atan

Arctangent in degrees. `math.atan` answers in radians.

```python
kitty.say(kitty.atan(1))
```

### kitty.ln

The natural log. `math.log(n)` is the same block.

```python
kitty.say(math.log(8))
```

### kitty.log

Log base 10. `math.log10(n)` is the same block.

```python
kitty.say(math.log10(100))
```

### kitty.exp

e raised to a power. `math.exp(n)` is the same block.

```python
kitty.say(math.exp(1))
```

### kitty.power10

10 raised to a power.

**n:** the exponent.

```python
kitty.say(kitty.power10(2))
```

### kitty.math

One Scratch math block, chosen by name. Prefer `math.sin` and the other math functions.

**op:** `abs`, `floor`, `ceiling`, `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `ln`, `log`, `e ^`, or `10 ^`.

**n:** the number. Angles for this block are in degrees. `math.sin` uses radians.

```python
kitty.say(kitty.math("sqrt", 9))
```

### kitty.length

The length of a list, a dictionary, or text. `len(value)` is the same block. On a grid, `len` reads the size of that dimension. On a dictionary, `len` is the number of keys.

**value:** a list, a dictionary, or text.

```python
kitty.say(len(items))
kitty.say(len(scores))
kitty.say(len("cat"))
```

### kitty.contains

True when a list or dictionary contains a value. `item in items` is the same block. For a dictionary, this searches the keys.

**container:** the list or dictionary.

**item:** the value to look for.

```python
if "worm" in items:
    kitty.say("yes")

if "ada" in scores:
    kitty.say(scores["ada"])
```

## Variables and lists

Declaring `score = 0`, `items = [1, 2]`, or `scores = {"ada": 3}` is enough when the Scratch name can match the Python name. Use these functions for a different Scratch name, a monitor, or a value shared by every sprite. List and dictionary behavior is in [Lists](#lists) and [Dictionaries](#dictionaries).

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

```python
items = kitty.list("items", ["worm"])
bag = kitty.list("bag", shared=True, show=True)
```

`items = ["worm"]` declares the same kind of list when the Scratch name can match the Python name. Indexes start at 0. Use `append`, `extend`, `insert`, `remove`, `pop`, `index`, and `clear` on the list.

### kitty.add

Add an item to a one-dimensional list. `items.append(item)` is the same block. This is not number addition.

**item:** the item.

**list:** the list.

```python
items.append("fish")
kitty.add(score, items)
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

## Messages

### kitty.broadcast

Send a message and keep going. Every `@kitty.when_receive` for that message starts, and this script does not wait for them.

**message:** the message name. The sender and the receiver have to use the same text.

```python
kitty.broadcast("go")
```

### kitty.broadcast_and_wait

Send a message and wait until every script that received it has finished. Use this when the next block should happen after the other sprites are done.

**message:** the message name.

```python
kitty.broadcast_and_wait("go")
```

## Pen

These blocks turn on the Pen extension.

### kitty.erase_all

Erase every pen mark.

```python
kitty.erase_all()
```

### kitty.stamp

Stamp this sprite's image onto the stage.

```python
kitty.stamp()
```

### kitty.pen_down

Put the pen down. The sprite draws as it moves.

```python
kitty.pen_down()
```

### kitty.pen_up

Pick the pen up.

```python
kitty.pen_up()
```

### kitty.set_pen_color

Set the pen color.

**color:** `"#rrggbb"`.

```python
kitty.set_pen_color("#ff0000")
```

### kitty.change_pen_color

Change the pen color by a number.

**amount:** how much to add.

```python
kitty.change_pen_color(10)
```

### kitty.set_pen_size

Set the pen size.

**size:** the size.

```python
kitty.set_pen_size(5)
```

### kitty.change_pen_size

Change the pen size.

**amount:** how much to add.

```python
kitty.change_pen_size(1)
```

### kitty.set_pen

Set one part of the pen.

**param:** `color`, `saturation`, `brightness`, or `transparency`.

**value:** the new amount.

```python
kitty.set_pen("color", 50)
kitty.set_pen("saturation", 50)
kitty.set_pen("brightness", 50)
kitty.set_pen("transparency", 50)
```

### kitty.change_pen

Change one part of the pen.

**param:** `color`, `saturation`, `brightness`, or `transparency`.

**value:** how much to add.

```python
kitty.change_pen("color", 10)
kitty.change_pen("transparency", 5)
```

## Costumes, sounds, and names

These add files. They are not stack blocks, and they do not belong inside a loop. Paths are relative to the script. Costume files are `svg`, `png`, or `jpg`. Sounds are usually `wav`.

When creating SVG artwork, center the subject in the SVG canvas. Scratch
uses `(0, 0)` as the stage center, not the top-left corner. A 64 x 64
costume should normally put its subject around `(32, 32)`. A 480 x 360
backdrop should normally put its central scene around `(240, 180)`.
See [The Scratch screen and SVG coordinates](#the-scratch-screen-and-svg-coordinates).

### kitty.costume

Add a costume to this sprite.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.costume("cat.svg")
kitty.costume("cat.svg", name="sitting")
kitty.switch_costume("sitting")
```

### kitty.sound

Add a sound to this sprite.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.sound("meow.wav")
kitty.sound("meow.wav", name="mew")
kitty.start_sound("mew")
```

### kitty.backdrop

Add a backdrop to the stage.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.backdrop("beach.svg")
kitty.backdrop("beach.svg", name="shore")
kitty.switch_backdrop("shore")
```

In a stage class, the call sits in the class body:

```python
class Game(kitty.Stage):
    kitty.backdrop("beach.svg", name="shore")

    @kitty.green_flag
    def start(self):
        self.switch_backdrop("shore")
```

In `stage.py` it is a top-level statement. With `@kitty.stage`, put it in that function, next to the hat:

```python
@kitty.stage
def setup():
    kitty.backdrop("beach.svg", name="shore")

    @kitty.green_flag
    def start():
        kitty.switch_backdrop("shore")
```

### kitty.sprite_name

Set this sprite's name.

**name:** the name Scratch shows.

```python
kitty.sprite_name("Felix")
```
