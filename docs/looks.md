## Looks

### kitty.say

Say a message.

**message:** text or a number.

```python
kitty.say("Hello world!")
kitty.say(score)
```

### kitty.say_for

Say a message, then clear it.

**message:** text or a number.

**seconds:** how long the bubble stays.

```python
kitty.say_for("hi", 2)
```

### kitty.think

Think a message.

**message:** text or a number.

```python
kitty.think("hmm")
```

### kitty.think_for

Think a message, then clear it.

**message:** text or a number.

**seconds:** how long the bubble stays.

```python
kitty.think_for("hmm", 2)
```

### kitty.switch_costume

Switch to a costume on this sprite.

**costume:** the costume's name.

```python
kitty.switch_costume("sitting")
```

### kitty.next_costume

Switch to the next costume.

```python
kitty.next_costume()
```

### kitty.switch_backdrop

Switch the stage's backdrop.

**backdrop:** the backdrop's name.

```python
kitty.switch_backdrop("beach")
```

### kitty.switch_backdrop_and_wait

Switch the backdrop and wait for scripts that start because of that switch.

**backdrop:** the backdrop's name.

```python
kitty.switch_backdrop_and_wait("beach")
```

### kitty.next_backdrop

Switch to the next backdrop.

```python
kitty.next_backdrop()
```

### kitty.change_size

Change the size percent.

**change:** how much to add.

```python
kitty.change_size(10)
```

### kitty.set_size

Set the size percent. `100` is normal size.

**size:** the percent.

```python
kitty.set_size(50)
```

### kitty.change_effect

Change a graphic effect. `color` shifts the costume's colors. `fisheye` bulges the middle. `whirl` twists it. `pixelate` makes it blocky. `mosaic` repeats it in a grid. `brightness` makes it lighter or darker. `ghost` makes it see-through: `0` is solid and `100` is invisible.

**effect:** `color`, `fisheye`, `whirl`, `pixelate`, `mosaic`, `brightness`, or `ghost`.

**change:** how much to add.

```python
kitty.change_effect("color", 25)
kitty.change_effect("ghost", 10)
```

### kitty.set_effect

Set a graphic effect to an amount. The effect names are the same as `change_effect`. `ghost` at `100` hides the sprite while it can still touch things. `hide` removes it from the stage.

**effect:** `color`, `fisheye`, `whirl`, `pixelate`, `mosaic`, `brightness`, or `ghost`.

**value:** the new amount.

```python
kitty.set_effect("ghost", 50)
```

### kitty.clear_graphic_effects

Clear every graphic effect.

```python
kitty.clear_graphic_effects()
```

### kitty.show

Show the sprite.

```python
kitty.show()
```

### kitty.hide

Hide the sprite.

```python
kitty.hide()
```

### kitty.go_to_layer

Move this sprite in front of the others, or behind them. `front` draws it on top. `back` draws it underneath.

**layer:** `front` or `back`.

```python
kitty.go_to_layer("front")
kitty.go_to_layer("back")
```

### kitty.go_layers

Step this sprite forward or backward through the pile of sprites. `forward` moves it toward the front by `number` places. `backward` moves it toward the back.

**direction:** `forward` or `backward`.

**number:** how many layers.

```python
kitty.go_layers("forward", 1)
kitty.go_layers("backward", 2)
```

### kitty.costume_number

The costume's number.

```python
kitty.say(kitty.costume_number())
```

### kitty.costume_name

The costume's name.

```python
kitty.say(kitty.costume_name())
```

### kitty.backdrop_number

The backdrop's number.

```python
kitty.say(kitty.backdrop_number())
```

### kitty.backdrop_name

The backdrop's name.

```python
kitty.say(kitty.backdrop_name())
```

### kitty.size

The size percent.

```python
kitty.say(kitty.size())
```
