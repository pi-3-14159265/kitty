# Choices and loops

Choices run code only when something is true. Loops run code several times.

## If, elif, and else

```python
if kitty.touching("mouse-pointer"):
    kitty.say("Boop!")
elif kitty.key_pressed("space"):
    kitty.move(10)
else:
    kitty.hide()
```

- `if` checks its condition first.
- `elif` checks a second choice.
- `else` runs if no earlier choice was true.
- Comparison values include `>`, `<`, `>=`, `<=`, `==`, and `!=`.

Use `and` for both conditions, `or` for either condition, and `not` for the
opposite condition.

```python
if score > 10 and kitty.touching("edge"):
    kitty.say("Great score!")
```

## Repeat a count

```python
for _ in range(10):
    kitty.move(10)
```

`range(10)` gives values `0` through `9`. To use the number, give it a name:

```python
for i in range(4):
    kitty.say(i)
```

This says `0`, `1`, `2`, and `3`.

You can choose start, stop, and step values:

```python
for i in range(1, 4):       # 1, 2, 3
    kitty.say(i)

for i in range(10, 0, -2):  # 10, 8, 6, 4, 2
    kitty.say(i)
```

The stop value is not included.

Range edge rules:

- `range(0)` and `range(3, 3)` run no times.
- An empty range does not create or change a loop variable.
- `range(10, 0)` runs no times because the default step is positive.
- Use a negative step when counting downward.
- A step of `0` is rejected at compile time.

## Repeat for items

```python
for item in items:
    kitty.say(item)
```

For a list, `item` is each list value.

```python
for name in scores:
    kitty.say(scores[name])
```

For a dictionary, `name` is each key. Use `scores[name]` to read its value.

## Repeat until a key or condition

```python
while not kitty.key_pressed("space"):
    kitty.move(10)
```

This is a Scratch repeat-until block. It runs until the space key is pressed.

```python
while True:
    kitty.move(10)
```

`while True` becomes a forever loop.

## Alternative `with` loops

The normal Python forms are usually easiest, but Kitty also supports:

```python
with kitty.repeat(10):
    kitty.move(10)

with kitty.repeat_until(kitty.key_pressed("space")):
    kitty.move(10)

with kitty.forever():
    kitty.move(10)

with kitty.if_(kitty.touching("edge")):
    kitty.hide()
```

`kitty.if_` has no `elif` or `else`. Use a Python `if` when you need them.
