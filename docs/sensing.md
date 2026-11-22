## Sensing

Colors are `"#rrggbb"`, six hex digits. The first pair is red, the next is green, and the last is blue. `00` is none and `ff` is full, so `"#ff0000"` is red, `"#00ff00"` is green, and `"#0000ff"` is blue.

### kitty.touching

True when the sprite is touching a target.

**target:** `mouse-pointer`, `edge`, or a sprite name.

```python
if kitty.touching("mouse-pointer"):
    kitty.say("boop")

if kitty.touching("edge"):
    kitty.if_on_edge_bounce()
```

### kitty.touching_color

True when the sprite is touching a color.

**color:** `"#rrggbb"`.

```python
if kitty.touching_color("#ff0000"):
    kitty.say("red")
```

### kitty.color_is_touching

True when a color on this sprite is touching another color.

**color:** the color on this sprite, `"#rrggbb"`.

**color2:** the other color, `"#rrggbb"`.

```python
if kitty.color_is_touching("#ff0000", "#00ff00"):
    kitty.hide()
```

### kitty.distance_to

The distance to a target.

**target:** `mouse-pointer`, or a sprite name.

```python
kitty.say(kitty.distance_to("mouse-pointer"))
```

### kitty.ask

Ask a question and wait. Read the reply with `kitty.answer`.

**question:** the question.

```python
kitty.ask("Your name?")
kitty.say(kitty.answer())
```

### kitty.answer

The text from the last `ask`.

```python
kitty.say(kitty.answer())
```

### kitty.key_pressed

True while a key is down.

**key:** `space`, `up arrow`, `down arrow`, `left arrow`, `right arrow`, `enter`, `any`, or a letter or digit. `up`, `down`, `left`, and `right` are the arrow keys.

```python
if kitty.key_pressed("space"):
    kitty.move(10)
```

### kitty.mouse_down

True while the mouse button is down.

```python
if kitty.mouse_down():
    kitty.say("click")
```

### kitty.mouse_x

The mouse x position.

```python
kitty.say(kitty.mouse_x())
```

### kitty.mouse_y

The mouse y position.

```python
kitty.say(kitty.mouse_y())
```

### kitty.set_drag_mode

Choose whether the viewer can drag this sprite.

**mode:** `draggable` or `not draggable`.

```python
kitty.set_drag_mode("draggable")
```

### kitty.loudness

How loud the microphone is.

```python
kitty.say(kitty.loudness())
```

### kitty.timer

Seconds since the timer was reset.

```python
kitty.say(kitty.timer())
```

### kitty.reset_timer

Set the timer back to 0.

```python
kitty.reset_timer()
```

### kitty.property_of

Read a property of a sprite or the stage.

**property:** `x position`, `y position`, `direction`, `costume #`, `costume name`, `size`, `volume`, `backdrop #`, or `backdrop name`.

**target:** a sprite name, or `stage`.

```python
kitty.say(kitty.property_of("x position", "Cat"))
kitty.say(kitty.property_of("costume name", "Cat"))
kitty.say(kitty.property_of("backdrop name", "stage"))
```

`x` and `y` also mean the positions. `costume number` and `backdrop number` mean `costume #` and `backdrop #`.

### kitty.current

The time on the computer running the project.

**unit:** `year`, `month`, `date`, `day of week`, `hour`, `minute`, or `second`.

```python
kitty.say(kitty.current("hour"))
kitty.say(kitty.current("day of week"))
```

### kitty.days_since_2000

Days since the year 2000.

```python
kitty.say(kitty.days_since_2000())
```

### kitty.username

The viewer's Scratch username.

```python
kitty.say(kitty.username())
```
