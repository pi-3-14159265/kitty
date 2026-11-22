## Costumes, sounds, and names

These add files. They are not stack blocks, and they do not belong inside a loop. Paths are relative to the script. Costume files are `svg`, `png`, or `jpg`. Sounds are usually `wav`.

When creating SVG artwork, center the subject in the SVG canvas. Scratch
uses `(0, 0)` as the stage center, not the top-left corner. A 64 x 64
costume should normally put its subject around `(32, 32)`. A 480 x 360
backdrop should normally put its central scene around `(240, 180)`.
See [The Scratch screen and SVG coordinates](motion.md#the-scratch-screen-and-svg-coordinates).

### kitty.costume

Add a costume to this sprite.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.costume("cat.svg")
kitty.costume("cat.svg", name="sitting")
kitty.switch_costume("sitting")
```

### kitty.sound

Add a sound to this sprite.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.sound("meow.wav")
kitty.sound("meow.wav", name="mew")
kitty.start_sound("mew")
```

### kitty.backdrop

Add a backdrop to the stage.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

```python
kitty.backdrop("beach.svg")
kitty.backdrop("beach.svg", name="shore")
kitty.switch_backdrop("shore")
```

In a stage class, the call sits in the class body:

```python
class Game(kitty.Stage):
    kitty.backdrop("beach.svg", name="shore")

    @kitty.green_flag
    def start(self):
        self.switch_backdrop("shore")
```

In `stage.py` it is a top-level statement. With `@kitty.stage`, put it in that function, next to the hat:

```python
@kitty.stage
def setup():
    kitty.backdrop("beach.svg", name="shore")

    @kitty.green_flag
    def start():
        kitty.switch_backdrop("shore")
```

### kitty.sprite_name

Set this sprite's name.

**name:** the name Scratch shows.

```python
kitty.sprite_name("Felix")
```
