## Motion

Menu targets accept a sprite name. `mouse` is the same as `mouse-pointer`.

### The Scratch screen and SVG coordinates

Scratch uses **screen coordinates**, not HTML/SVG page coordinates:

- the actual center of the screen is `(0, 0)`
- x increases to the right, from `-240` to `240`
- y increases upward, from `-180` to `180`
- the top-left of the stage is approximately `(-240, 180)`
- the bottom-right of the stage is approximately `(240, -180)`

Consequently, `kitty.go_to_xy(0, 0)` places a sprite at the center of the
screen. It does not place the sprite at the top-left or in the corner.

SVG artwork is also easier to use if its visible subject is centered in the
SVG canvas. The image itself does not use Scratch coordinates: a 64 x 64
costume is not drawn with `(0, 0)` at its top-left in Scratch. A full stage
backdrop is commonly 480 x 360, with its pixel center at `(240, 180)` inside
the SVG. Scratch maps that center to screen coordinate `(0, 0)`.

For example, this costume is intentionally centered around SVG point
`(32, 32)`:

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="24" fill="#4C97FF"/>
</svg>
```

This is more reliable than drawing the subject in a corner and using an
offset in Python. If the subject is a 64 x 64 circle whose center is
`(32, 32)`, placing the sprite at `(0, 0)` puts the circle at the center of
the screen.

PNG and JPG images work the same way: the middle pixel of the image sits on
the sprite's x and y, and one pixel is one step. See
[Bitmap images (PNG and JPG)](costumes-sounds-and-names.md#bitmap-images-png-and-jpg).

For a 480 x 360 backdrop, keep the scene centered around `(240, 180)`:

```svg
<svg xmlns="http://www.w3.org/2000/svg"
     width="480" height="360" viewBox="0 0 480 360">
  <rect width="480" height="360" fill="#78B84A"/>
  <circle cx="240" cy="180" r="30" fill="#FFFFFF"/>
</svg>
```

Do not convert SVG coordinates directly into Kitty coordinates. An SVG point
such as `(240, 180)` is a pixel position in the image; Scratch screen
coordinate `(0, 0)` is the stage center. Kitty movement functions such as
`kitty.go_to_xy(0, 0)` and `self.go_to_xy(0, 0)` always use Scratch screen
coordinates.

### kitty.move

Move the sprite.

**steps:** how many steps to move.

```python
kitty.move(10)
kitty.move(score)
```

### kitty.turn_right

Turn right.

**degrees:** how far to turn.

```python
kitty.turn_right(15)
```

### kitty.turn_left

Turn left.

**degrees:** how far to turn.

```python
kitty.turn_left(15)
```

### kitty.go_to

Go straight to a target.

**target:** `mouse-pointer`, `random position`, or a sprite name.

```python
kitty.go_to("mouse-pointer")
kitty.go_to("random position")
kitty.go_to("Cat")
```

### kitty.go_to_xy

Go to an x and y position.

**x:** the x position.

**y:** the y position.

```python
kitty.go_to_xy(0, 0)
kitty.go_to_xy(kitty.mouse_x(), kitty.mouse_y())
```

### kitty.glide_to

Glide to a target.

**seconds:** how long the glide takes.

**target:** `mouse-pointer`, `random position`, or a sprite name.

```python
kitty.glide_to(1, "mouse-pointer")
kitty.glide_to(0.5, "random position")
```

### kitty.glide_to_xy

Glide to an x and y position.

**seconds:** how long the glide takes.

**x:** the x position.

**y:** the y position.

```python
kitty.glide_to_xy(1, 0, 0)
```

### kitty.point_in_direction

Point in a direction. `90` is right, `0` is up, `-90` is left, and `180` is down. These degrees are the sprite's direction. They are separate from `math.sin`, which uses radians.

**direction:** degrees.

```python
kitty.point_in_direction(90)
```

### kitty.point_towards

Point towards a target. There is no random position on this block.

**target:** `mouse-pointer`, or a sprite name.

```python
kitty.point_towards("mouse-pointer")
kitty.point_towards("Cat")
```

### kitty.change_x

Change x.

**dx:** how much to add.

```python
kitty.change_x(10)
```

### kitty.set_x

Set x.

**x:** the new position.

```python
kitty.set_x(0)
```

### kitty.change_y

Change y.

**dy:** how much to add.

```python
kitty.change_y(10)
```

### kitty.set_y

Set y.

**y:** the new position.

```python
kitty.set_y(0)
```

### kitty.if_on_edge_bounce

If the sprite is on the edge, bounce.

```python
kitty.if_on_edge_bounce()
```

### kitty.set_rotation_style

Choose what the costume does when the sprite turns. `all around` spins the costume to match the direction, so it can end up upside down. `left-right` flips between facing left and facing right, which fits a side-view character. `don't rotate` leaves the costume upright while the direction still changes. `point_towards` and `move` still use that direction.

**style:** `left-right`, `all around`, or `don't rotate`.

```python
kitty.set_rotation_style("left-right")
kitty.set_rotation_style("all around")
kitty.set_rotation_style("don't rotate")
```

### kitty.x_position

The sprite's x position. On another sprite, `mouse.x_position()` is `x position of mouse`.

```python
kitty.say(kitty.x_position())
```

### kitty.y_position

The sprite's y position.

```python
kitty.say(kitty.y_position())
```

### kitty.direction

The sprite's direction.

```python
kitty.say(kitty.direction())
```
