## Events

A hat starts a script when something happens. It sits on a function or on a method. A function keeps one hat. Hats do not take inputs. Custom blocks, which you call yourself, are [Functions](functions.md#functions).

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

Define a custom block that you call by name. It does not return an answer. A `def` with no decorator and no `return` is the same kind of block. A default of `True` or `False`, or a `bool` note, makes a boolean input. Other defaults are numbers or text. A list or a dictionary cannot be a default. See [Defaults](functions.md#defaults).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `@kitty.block(warp=False)` draws the screen after each pass of a loop instead, like a Scratch custom block with "Run without screen refresh" off. See [Screen refresh](functions.md#screen-refresh).

```python
@kitty.block
def greet(name, loud=False):
    kitty.say(name)
```

### kitty.number

Define a custom block that returns a number or text. The body uses `return`. A `def` that returns a number or text is the same kind of block, even without this decorator. See [Answers](functions.md#answers).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `warp=False` draws the screen after each pass of a loop.

```python
@kitty.number
def double(n):
    return n * 2
```

### kitty.boolean

Define a custom block that returns true or false. Use it in `if`. The body uses `return` with a comparison, `and`, `or`, `not`, `True`, or `False`. See [Answers](functions.md#answers).

The block runs without screen refresh until it finishes or reaches `kitty.wait`. `warp=False` draws the screen after each pass of a loop.

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

A class that inherits `kitty.Sprite` is a sprite. See [Sprites](sprites.md#sprites).

### kitty.Stage

A class that inherits `kitty.Stage` is the stage. Backdrop declarations belong here. See [Sprites](sprites.md#sprites).
