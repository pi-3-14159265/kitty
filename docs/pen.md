## Pen

These blocks turn on the Pen extension.

### kitty.erase_all

Erase every pen mark.

```python
kitty.erase_all()
```

### kitty.stamp

Stamp this sprite's image onto the stage.

```python
kitty.stamp()
```

### kitty.pen_down

Put the pen down. The sprite draws as it moves.

```python
kitty.pen_down()
```

### kitty.pen_up

Pick the pen up.

```python
kitty.pen_up()
```

### kitty.set_pen_color

Set the pen color.

**color:** `"#rrggbb"`.

```python
kitty.set_pen_color("#ff0000")
```

### kitty.change_pen_color

Change the pen color by a number.

**amount:** how much to add.

```python
kitty.change_pen_color(10)
```

### kitty.set_pen_size

Set the pen size.

**size:** the size.

```python
kitty.set_pen_size(5)
```

### kitty.change_pen_size

Change the pen size.

**amount:** how much to add.

```python
kitty.change_pen_size(1)
```

### kitty.set_pen

Set one part of the pen.

**param:** `color`, `saturation`, `brightness`, or `transparency`.

**value:** the new amount.

```python
kitty.set_pen("color", 50)
kitty.set_pen("saturation", 50)
kitty.set_pen("brightness", 50)
kitty.set_pen("transparency", 50)
```

### kitty.change_pen

Change one part of the pen.

**param:** `color`, `saturation`, `brightness`, or `transparency`.

**value:** how much to add.

```python
kitty.change_pen("color", 10)
kitty.change_pen("transparency", 5)
```
