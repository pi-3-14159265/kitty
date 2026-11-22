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
