# Functions

A function is a reusable set of steps. A function with a decorator such as
`@kitty.green_flag` starts on its own. A normal function is called by name.

## First custom block

```python
import kitty

def greet(name):
    kitty.say("Hello " + name)

greet("Ada")
```

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

Each run of `items = []` or `scores = {}` builds a new list or dictionary for that call. A call to itself gets its own. `return items` hands that same list back, and the caller keeps it. Two names can also point at one list. See [Two names, one list](lists.md#two-names-one-list).

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

Call a number or boolean method on the sprite that defines it. `mouse.score_plus(3)` does not work, because the saved answer stays on the mouse. A method that does not return can be called on another sprite. That sends a message and waits. See [Sprites](sprites.md#sprites).

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
