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
