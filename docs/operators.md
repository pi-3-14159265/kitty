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
