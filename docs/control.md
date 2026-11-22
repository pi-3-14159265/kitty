## Control

### kitty.wait

Pause this script. Other scripts can run during the pause. Inside a custom block, this is also what lets the screen draw between steps. See [Screen refresh](functions.md#screen-refresh).

**seconds:** how long to wait.

```python
kitty.wait(1)
kitty.wait(0.1)
```

### kitty.repeat

Repeat a `with` block. `for _ in range(n)` is the same block. `for i in range(...)` also sets `i`. See [Choices and loops](choices-and-loops.md#choices-and-loops).

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
