## Costumes, sounds, and names

These add files. They are not stack blocks, and they do not belong inside a loop. Paths are relative to the script. Costume and backdrop files are `svg`, `png`, or `jpg`. Sounds are usually `wav`.

Kitty puts the middle of a costume image on the sprite's x and y, and the middle of a backdrop on the middle of the stage. Scratch uses `(0, 0)` as the stage center, not the top-left corner, so `kitty.go_to_xy(0, 0)` shows the middle of the costume at the middle of the stage.

- An SVG is drawn at any size. Center the subject in the SVG canvas: a 64 x 64 costume should normally put its subject around `(32, 32)`, and a 480 x 360 backdrop around `(240, 180)`. See [The Scratch screen and SVG coordinates](motion.md#the-scratch-screen-and-svg-coordinates).
- A PNG or JPG is a bitmap: a grid of pixels. One pixel is one Scratch step. See [Bitmap images (PNG and JPG)](#bitmap-images-png-and-jpg).

### kitty.costume

Add a costume to this sprite.

**path:** the file, relative to the script.

**name:** the Scratch name. Omit it to use the file name.

**resolution:** PNG and JPG only. `1` shows one image pixel per step. `2` shows the image at half its pixel size. The default is `1`. See [Drawn at double size](#drawn-at-double-size).

**center:** the point of the image that sits on the sprite's x and y, and that the sprite turns around, as `(x, y)` from the image's top-left. For a PNG or JPG it is in image pixels. Omit it to use the middle of the image.

```python
kitty.costume("cat.svg")
kitty.costume("cat.png", name="sitting")
kitty.costume("cat-big.png", resolution=2)
kitty.costume("pendulum.svg", center=(32, 0))
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

**resolution:** PNG and JPG only. `2` shows the image at half its pixel size, so a 960 x 720 backdrop fills the stage. The default is `1`.

```python
kitty.backdrop("beach.svg")
kitty.backdrop("beach.png", name="shore")
kitty.backdrop("night-960.png", resolution=2)
kitty.switch_backdrop("shore")
```

In a stage class, the call sits in the class body:

```python
class Game(kitty.Stage):
    kitty.backdrop("beach.png", name="shore")

    @kitty.green_flag
    def start(self):
        self.switch_backdrop("shore")
```

In `stage.py` it is a top-level statement. With `@kitty.stage`, put it in that function, next to the hat:

```python
@kitty.stage
def setup():
    kitty.backdrop("beach.png", name="shore")

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

### kitty.start_with

How this sprite, or the stage, starts when the project opens. This is not a block: it is what the Scratch editor saves with a sprite. Leave out anything that should start as usual.

**x**, **y:** where the sprite starts. The default is `0, 0`.

**direction:** the default is `90`, pointing right.

**size:** in percent. The default is `100`.

**visible:** `False` starts the sprite hidden.

**costume:** the name of the costume to start with.

**rotation_style:** `"all around"`, `"left-right"`, or `"don't rotate"`.

**draggable:** `True` lets the player drag the sprite.

**volume:** in percent. The default is `100`.

**layer:** `1` is the back layer, then `2`, and so on. Sprites without a layer go in front of these, in file order.

On the stage, use **backdrop** (the name of the backdrop to start with), **volume**, and **tempo**.

```python
kitty.start_with(x=-100, y=20, size=50, costume="walk2", visible=False, layer=2)
```

```python
# stage.py
kitty.start_with(backdrop="night", tempo=90)
```

### Bitmap images (PNG and JPG)

A PNG or JPG file works as a costume or a backdrop. Put the file next to the script and name it in `kitty.costume` or `kitty.backdrop`:

```text
game/
    cat.py
    cat.png
    stage.py
    park.jpg
```

```python
# cat.py
import kitty

kitty.costume("cat.png")

@kitty.green_flag
def start():
    kitty.go_to_xy(0, 0)
    kitty.say("Meow!")
```

```python
# stage.py
import kitty

kitty.backdrop("park.jpg")
```

```bash
kitty build game/
```

#### Size

One image pixel is one Scratch step. The stage is 480 steps wide and 360 steps tall.

| Image file | On the stage |
| --- | --- |
| 100 x 60 PNG costume | 100 steps wide, 60 steps tall |
| 480 x 360 PNG or JPG backdrop | fills the stage |
| 400 x 300 backdrop | centered, with an empty border |
| 960 x 720 backdrop with `resolution=2` | fills the stage |

Change the size while the project runs with `kitty.set_size(50)` or `kitty.change_size(10)`. Scratch smooths a bitmap that is drawn larger than its pixels, so start with an image at least as big as the sprite will look.

The compiler warns when an image shows bigger than the stage:

```text
warning: cat.py:3: photo.jpg shows as 4032 x 3024, bigger than the 480 x 360 stage. Use a smaller image, resolution=2, or kitty.set_size
```

Shrink the image in a paint program before you build. A big photo also makes a big `.sb3` file.

#### Where the middle is

The middle pixel of the image sits on the sprite's x and y. Crop the image so the character is in the middle, with even space around it. The sprite turns around that middle too, so a character drawn in one corner swings around an empty point when it turns.

A phone photo often stores its pixels sideways, with a note to turn it. Kitty reads that note, so the middle and the size match the photo as you see it.

#### Transparent backgrounds

A PNG keeps transparent pixels, so a character drawn on a transparent background shows only the character. A JPG has no transparency: a JPG costume is always a full rectangle. Use PNG for characters and JPG for photos and backdrops.

`kitty.touching` and `kitty.touching_color` look at the pixels that show. Transparent pixels in a PNG do not touch anything.

#### Drawn at double size

Scratch stores its own bitmap costumes at double size, two image pixels per step, so they stay sharp. Use `resolution=2` for an image made that way:

- a bitmap costume or backdrop taken out of a Scratch project, for example by `kitty decomp`;
- a 960 x 720 backdrop;
- art you drew at double size so it stays sharp when it grows.

```python
kitty.costume("costumes/cat-a.png", resolution=2)
kitty.backdrop("Stage/costumes/blue-sky.png", resolution=2)
```

An SVG has no pixels, so `resolution` is only for PNG and JPG.

#### Other image files

GIF, BMP, WEBP, and other formats are rejected:

```text
cat.py:3: cat.gif: a costume is an svg, png, or jpg file
```

Open the image in a paint program and save it as PNG. For an animated GIF, save each frame as its own PNG and add each one as a costume:

```python
kitty.costume("walk1.png")
kitty.costume("walk2.png")

@kitty.green_flag
def start():
    while True:
        kitty.next_costume()
        kitty.wait(0.2)
```

Kitty reads the file itself to tell a PNG from a JPG, so a PNG saved as `cat.jpg` still works.
