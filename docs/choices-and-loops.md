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
