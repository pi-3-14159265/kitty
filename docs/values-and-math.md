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
