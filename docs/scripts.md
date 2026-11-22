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
