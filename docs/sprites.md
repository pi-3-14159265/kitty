## Sprites

Unless it declares a decorated target or sprite instances, a plain script
becomes one sprite named after the file. A file named `stage.py` is the stage.
A project can have only one stage.

A class that inherits `kitty.Sprite` is a sprite. A class that inherits `kitty.Stage` is the stage. `self.hp = 9` is a variable on that sprite. A method is a custom block, unless it has a hat decorator. The first parameter must be named `self`, and it is left off the Scratch block. Hat methods cannot take more parameters.

```python
import kitty

class Animal(kitty.Sprite):
    title = "pet"

    def __init__(self):
        self.hp = 1

    def speak(self):
        self.say(self.title)

class Cat(Animal):
    def __init__(self, lives):
        super().__init__()
        self.hp = lives
        self.say("born")

    def speak(self):
        super().speak()
        self.say("meow")

    @kitty.green_flag
    def start(self):
        self.speak()
        self.move(10)

felix = Cat(9)
mittens = Cat(3)
```

`felix = Cat(9)` and `mittens = Cat(3)` are two sprites. `hp` starts at the value passed in. `title` starts as `"pet"`. `speak` is a custom block. `start` runs when the green flag is clicked, and `say "born"` from `__init__` is placed at the front of that script. Constructor arguments must be numbers, text, or lists, because each instance is baked into the project. Scratch clones share one sprite, so Kitty does not turn instances into clones.

If you never write `felix = Cat()`, the class itself becomes one sprite named `Cat`. A class that only exists so other classes can inherit it does not become its own sprite.

```python
class Game(kitty.Stage):
    @kitty.green_flag
    def start(self):
        self.switch_backdrop("backdrop1")
```

`super().speak()` compiles the parent method under its own name, `Animal speak`, and calls that block.

A call on another sprite waits for that sprite to run the method:

```python
class Mouse(kitty.Sprite):
    def squeak(self, word):
        self.say(word)

class Cat(kitty.Sprite):
    @kitty.green_flag
    def start(self):
        mouse.squeak("hi")
        self.say(mouse.x_position())

mouse = Mouse()
```

`mouse.squeak("hi")` copies each number or piece of text into a shared variable, sends the mouse a message, and waits until that script finishes. A variable that holds a number or text is copied the same way. A `True` or `False` input is refused. A list arrives as one piece of text, the items stuck together, so pass a number or text when the other sprite needs the value itself. A method that returns a number or a condition stays on the sprite that defines it, so call that method with `self`.

`mouse.x_position()` reads `x position of mouse`. The same readers are `y_position`, `direction`, `size`, `costume_number`, `costume_name`, and `volume`.

Another sprite's variables stay on that sprite. Share a variable by declaring it with `shared=True`:

```python
score = kitty.variable("score", 0, shared=True)

class Cat(kitty.Sprite):
    @kitty.green_flag
    def start(self):
        global score
        score += 1
```

Every block function is also a method, so `self.say("hi")` is `kitty.say("hi")`. `self.clone()` creates a clone of this sprite. Declarations, hat decorators, `kitty.length`, `kitty.contains`, and `kitty.math` stay on `kitty`.

A sprite with no costume gets a blue circle. A stage with no backdrop gets a white backdrop named `backdrop1`.
