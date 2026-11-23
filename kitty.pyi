"""Scratch blocks for scripts compiled with comp.py.

Menu arguments list their choices in the editor. Type the opening quote
and pick a value.
"""

from collections.abc import Callable
from inspect import Parameter, Signature
from typing import Any, Literal, TypeVar, overload

F = TypeVar("F", bound=Callable[..., Any])

Number = int | float
Value = int | float | str
Effect = Literal["color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", "ghost"]
SoundEffect = Literal["pitch", "pan left/right", "pan"]
RotationStyle = Literal["left-right", "all around", "don't rotate", "left_right", "all_around", "dont rotate", "dont_rotate"]
StopOption = Literal["all", "this script", "other scripts in sprite", "this_script", "other scripts", "other_scripts"]
DragMode = Literal["draggable", "not draggable", "not_draggable"]
Layer = Literal["front", "back"]
LayerDirection = Literal["forward", "backward"]
TimeUnit = Literal["year", "month", "date", "day of week", "hour", "minute", "second", "dayofweek"]
PenParam = Literal["color", "saturation", "brightness", "transparency"]
Property = Literal[
    "x position",
    "y position",
    "direction",
    "costume #",
    "costume name",
    "size",
    "volume",
    "backdrop #",
    "backdrop name",
    "x",
    "y",
    "costume number",
    "backdrop number",
]
MathOp = Literal["abs", "floor", "ceiling", "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "e ^", "10 ^"]
Index = int | float | Literal["last", "all", "random"]
Key = Literal['space', 'up arrow', 'down arrow', 'left arrow', 'right arrow', 'up', 'down', 'left', 'right', 'enter', 'any', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] | str
GoTarget = Literal["mouse-pointer", "random position", "mouse", "mouse_pointer", "random_position"] | str
PointTarget = Literal["mouse-pointer", "mouse", "mouse_pointer"] | str
TouchTarget = Literal["mouse-pointer", "edge", "mouse", "mouse_pointer"] | str
DistanceTarget = Literal["mouse-pointer", "mouse", "mouse_pointer"] | str
CloneTarget = Literal["myself"] | str
ObjectTarget = Literal["stage"] | str


class _With:
    """The body of a with statement."""

    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...



@overload
def green_flag(fn: F) -> F:
    """Run this function when the green flag is clicked.

    Two green-flag scripts run at the same time. Top-level statements are already one of them.
    """
    ...

@overload
def green_flag() -> Callable[[F], F]: ...

def when_key(key: Key) -> Callable[[F], F]:
    """Run this function when a key is pressed.

    Args:
        key: "space", "up arrow", "down arrow", "left arrow", "right arrow", "enter", "any", or a letter or digit. "up", "down", "left", and "right" are the arrow keys.
    """
    ...

def when_clicked(fn: F) -> F:
    """Run this function when this sprite is clicked. On the stage, when the stage is clicked."""
    ...

def when_stage_clicked(fn: F) -> F:
    """Run this function when the stage is clicked."""
    ...

def when_backdrop(name: str) -> Callable[[F], F]:
    """Run this function when the backdrop switches to this name.

    Args:
        name: The backdrop's name.
    """
    ...

def when_loudness(value: Value) -> Callable[[F], F]:
    """Run this function when the loudness is greater than this number.

    Args:
        value: The loudness to pass.
    """
    ...

def when_timer(value: Value) -> Callable[[F], F]:
    """Run this function when the timer is greater than this number.

    Args:
        value: Seconds on the timer.
    """
    ...

def when_receive(message: str) -> Callable[[F], F]:
    """Run this function when this message is broadcast.

    Args:
        message: The message name.
    """
    ...

def when_cloned(fn: F) -> F:
    """Run this function when this sprite starts as a clone."""
    ...

@overload
def block(fn: F) -> F:
    """Define a custom Scratch block. A bool default or annotation makes a boolean input."""
    ...

@overload
def block(*, warp: bool = False) -> Callable[[F], F]:
    """Define a custom Scratch block.

    Args:
        warp: Accepted, and ignored. Custom blocks always run without screen refresh.
    """
    ...

@overload
def number(fn: F) -> F:
    """Define a custom block that returns a number or text. Use return."""
    ...

@overload
def number(*, warp: bool = False) -> Callable[[F], F]:
    """Define a custom block that returns a number or text. Use return.

    Args:
        warp: Accepted, and ignored. Custom blocks always run without screen refresh.
    """
    ...

@overload
def boolean(fn: F) -> F:
    """Define a custom block that returns a condition. Use return."""
    ...

@overload
def boolean(*, warp: bool = False) -> Callable[[F], F]:
    """Define a custom block that returns a condition. Use return.

    Args:
        warp: Accepted, and ignored. Custom blocks always run without screen refresh.
    """
    ...

@overload
def sprite(fn: F) -> F:
    """Put this function's scripts on a sprite named after the function."""
    ...

@overload
def sprite(name: str) -> Callable[[F], F]:
    """Put this function's scripts on a sprite.

    Args:
        name: The sprite's name.
    """
    ...

def stage(fn: F) -> F:
    """Put this function's scripts on the stage. A project can have only one stage."""
    ...

@overload
def ignore(fn: F) -> F:
    """Skip this Python-only function. It is not compiled into Scratch."""
    ...

@overload
def ignore() -> Callable[[F], F]:
    """Skip this Python-only function. It is not compiled into Scratch."""
    ...

def move(steps: Value) -> None:
    """Move the sprite by a number of steps.

    Args:
        steps: How many steps to move.
    """
    ...

def turn_right(degrees: Value) -> None:
    """Turn the sprite to the right.

    Args:
        degrees: How many degrees to turn.
    """
    ...

def turn_left(degrees: Value) -> None:
    """Turn the sprite to the left.

    Args:
        degrees: How many degrees to turn.
    """
    ...

def go_to(target: GoTarget) -> None:
    """Go to a sprite, the mouse, or a random position.

    Args:
        target: "mouse-pointer", "random position", or a sprite name.
    """
    ...

def go_to_xy(x: Value, y: Value) -> None:
    """Go to an x and y position.

    Args:
        x: The x position.
        y: The y position.
    """
    ...

def glide_to(seconds: Value, target: GoTarget) -> None:
    """Glide to a sprite, the mouse, or a random position.

    Args:
        seconds: How long the glide takes.
        target: "mouse-pointer", "random position", or a sprite name.
    """
    ...

def glide_to_xy(seconds: Value, x: Value, y: Value) -> None:
    """Glide to an x and y position.

    Args:
        seconds: How long the glide takes.
        x: The x position.
        y: The y position.
    """
    ...

def point_in_direction(direction: Value) -> None:
    """Point the sprite in a direction. 90 is right.

    Args:
        direction: The direction in degrees.
    """
    ...

def point_towards(target: PointTarget) -> None:
    """Point towards the mouse or a sprite.

    Args:
        target: "mouse-pointer" or a sprite name.
    """
    ...

def change_x(dx: Value) -> None:
    """Change x by a number.

    Args:
        dx: How much to add to x.
    """
    ...

def set_x(x: Value) -> None:
    """Set x to a number.

    Args:
        x: The new x position.
    """
    ...

def change_y(dy: Value) -> None:
    """Change y by a number.

    Args:
        dy: How much to add to y.
    """
    ...

def set_y(y: Value) -> None:
    """Set y to a number.

    Args:
        y: The new y position.
    """
    ...

def if_on_edge_bounce() -> None:
    """If the sprite is on the edge, bounce."""
    ...

def set_rotation_style(style: RotationStyle) -> None:
    """Set how the sprite rotates.

    Args:
        style: "left-right", "all around", or "don't rotate".
    """
    ...

def x_position() -> Number:
    """Return the sprite's x position."""
    ...

def y_position() -> Number:
    """Return the sprite's y position."""
    ...

def direction() -> Number:
    """Return the sprite's direction."""
    ...

def say(message: Value) -> None:
    """Say a message in a speech bubble.

    Args:
        message: Text or a number to show.
    """
    ...

def say_for(message: Value, seconds: Value) -> None:
    """Say a message, then clear it.

    Args:
        message: Text or a number to show.
        seconds: How long the bubble stays.
    """
    ...

def think(message: Value) -> None:
    """Think a message in a thought bubble.

    Args:
        message: Text or a number to show.
    """
    ...

def think_for(message: Value, seconds: Value) -> None:
    """Think a message, then clear it.

    Args:
        message: Text or a number to show.
        seconds: How long the bubble stays.
    """
    ...

def switch_costume(costume: str) -> None:
    """Switch to a costume on this sprite.

    Args:
        costume: The costume's name.
    """
    ...

def next_costume() -> None:
    """Switch to the next costume."""
    ...

def switch_backdrop(backdrop: str) -> None:
    """Switch the stage backdrop.

    Args:
        backdrop: The backdrop's name.
    """
    ...

def switch_backdrop_and_wait(backdrop: str) -> None:
    """Switch the backdrop and wait for other scripts that start because of it.

    Args:
        backdrop: The backdrop's name.
    """
    ...

def next_backdrop() -> None:
    """Switch to the next backdrop."""
    ...

def change_size(change: Value) -> None:
    """Change the sprite's size.

    Args:
        change: How much to add to the size.
    """
    ...

def set_size(size: Value) -> None:
    """Set the sprite's size. 100 is normal.

    Args:
        size: The size, as a percent.
    """
    ...

def change_effect(effect: Effect, change: Value) -> None:
    """Change a graphic effect.

    Args:
        effect: "color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", or "ghost".
        change: How much to add.
    """
    ...

def set_effect(effect: Effect, value: Value) -> None:
    """Set a graphic effect.

    Args:
        effect: "color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", or "ghost".
        value: The new amount.
    """
    ...

def clear_graphic_effects() -> None:
    """Clear every graphic effect."""
    ...

def show() -> None:
    """Show the sprite."""
    ...

def hide() -> None:
    """Hide the sprite."""
    ...

def go_to_layer(layer: Layer) -> None:
    """Go to the front or back layer.

    Args:
        layer: "front" or "back".
    """
    ...

def go_layers(direction: LayerDirection, number: Value) -> None:
    """Move forward or backward a number of layers.

    Args:
        direction: "forward" or "backward".
        number: How many layers to move.
    """
    ...

def costume_number() -> Number:
    """Return the costume number."""
    ...

def costume_name() -> Value:
    """Return the costume name."""
    ...

def backdrop_number() -> Number:
    """Return the backdrop number."""
    ...

def backdrop_name() -> Value:
    """Return the backdrop name."""
    ...

def size() -> Number:
    """Return the sprite's size."""
    ...

def play_until_done(sound: str) -> None:
    """Play a sound and wait until it finishes.

    Args:
        sound: The sound's name.
    """
    ...

def start_sound(sound: str) -> None:
    """Start a sound without waiting.

    Args:
        sound: The sound's name.
    """
    ...

def stop_all_sounds() -> None:
    """Stop every sound."""
    ...

def change_sound_effect(effect: SoundEffect, value: Value) -> None:
    """Change a sound effect.

    Args:
        effect: "pitch" or "pan left/right".
        value: How much to add.
    """
    ...

def set_sound_effect(effect: SoundEffect, value: Value) -> None:
    """Set a sound effect.

    Args:
        effect: "pitch" or "pan left/right".
        value: The new amount.
    """
    ...

def clear_sound_effects() -> None:
    """Clear every sound effect."""
    ...

def change_volume(amount: Value) -> None:
    """Change the volume.

    Args:
        amount: How much to add.
    """
    ...

def set_volume(percent: Value) -> None:
    """Set the volume. 100 is full.

    Args:
        percent: The volume, as a percent.
    """
    ...

def volume() -> Number:
    """Return the volume."""
    ...

def wait(seconds: Value) -> None:
    """Wait a number of seconds.

    Args:
        seconds: How long to wait.
    """
    ...

def repeat(times: Value) -> _With:
    """Repeat the with-block a number of times. for _ in range(n) is the same block.

    Args:
        times: How many times to repeat.
    """
    ...

def forever() -> _With:
    """Repeat the with-block forever. while True is the same block."""
    ...

def if_(condition: bool) -> _With:
    """Run the with-block when the condition is true. A Python if can also have elif and else.

    Args:
        condition: A comparison, touching, or other boolean block.
    """
    ...

def repeat_until(condition: bool) -> _With:
    """Repeat the with-block until the condition is true.

    Args:
        condition: A comparison, touching, or other boolean block.
    """
    ...

def wait_until(condition: bool) -> None:
    """Wait until the condition is true.

    Args:
        condition: A comparison, touching, or other boolean block.
    """
    ...

def stop(what: StopOption) -> None:
    """Stop scripts.

    Args:
        what: "all", "this script", or "other scripts".
    """
    ...

def create_clone(target: CloneTarget = "myself") -> None:
    """Create a clone of this sprite or another sprite.

    Args:
        target: "myself" or a sprite name.
    """
    ...

def delete_clone() -> None:
    """Delete this clone."""
    ...

def touching(target: TouchTarget) -> bool:
    """True when the sprite touches a target.

    Args:
        target: "mouse-pointer", "edge", or a sprite name.
    """
    ...

def touching_color(color: str) -> bool:
    """True when the sprite touches a color.

    Args:
        color: A color written "#rrggbb", such as "#ff0000".
    """
    ...

def color_is_touching(color: str, color2: str) -> bool:
    """True when one color on this sprite touches another color.

    Args:
        color: The color on this sprite, "#rrggbb".
        color2: The other color, "#rrggbb".
    """
    ...

def distance_to(target: DistanceTarget) -> Number:
    """Distance to the mouse or a sprite.

    Args:
        target: "mouse-pointer" or a sprite name.
    """
    ...

def ask(question: Value) -> None:
    """Ask a question and wait. The reply is kitty.answer().

    Args:
        question: The question to ask.
    """
    ...

def answer() -> Value:
    """The reply from the last ask."""
    ...

def key_pressed(key: Key) -> bool:
    """True while a key is pressed.

    Args:
        key: "space", "up arrow", "down arrow", "left arrow", "right arrow", "enter", "any", or a letter or digit. "up", "down", "left", and "right" are the arrow keys.
    """
    ...

def mouse_down() -> bool:
    """True while the mouse button is down."""
    ...

def mouse_x() -> Number:
    """The mouse x position."""
    ...

def mouse_y() -> Number:
    """The mouse y position."""
    ...

def set_drag_mode(mode: DragMode) -> None:
    """Let the viewer drag this sprite, or not.

    Args:
        mode: "draggable" or "not draggable".
    """
    ...

def loudness() -> Number:
    """How loud the microphone is."""
    ...

def timer() -> Number:
    """Seconds since the timer was reset."""
    ...

def reset_timer() -> None:
    """Reset the timer."""
    ...

def property_of(property: Property, target: ObjectTarget) -> Value:
    """Read a property of a sprite or the stage.

    Args:
        property: "x position", "y position", "direction", "costume #", "costume name", "size", "volume", "backdrop #", or "backdrop name".
        target: A sprite name, or "stage".
    """
    ...

def current(unit: TimeUnit) -> Number:
    """The current year, month, date, day of the week, hour, minute, or second.

    Args:
        unit: "year", "month", "date", "day of week", "hour", "minute", or "second".
    """
    ...

def days_since_2000() -> Number:
    """Days since 2000."""
    ...

def username() -> Value:
    """The Scratch username of the viewer."""
    ...

def subtract(a: Value, b: Value) -> Number:
    """Subtract two numbers. a - b is the same block.

    Args:
        a: The number to subtract from.
        b: The number to subtract.
    """
    ...

def multiply(a: Value, b: Value) -> Number:
    """Multiply two numbers. a * b is the same block.

    Args:
        a: The first number.
        b: The second number.
    """
    ...

def divide(a: Value, b: Value) -> Number:
    """Divide two numbers. a / b is the same block.

    Args:
        a: The number to divide.
        b: The number to divide by.
    """
    ...

def random(start: Value, end: Value) -> Number:
    """Pick a random number from start through end.

    Args:
        start: The low end.
        end: The high end.
    """
    ...

def greater(a: Value, b: Value) -> bool:
    """True when a is greater than b. a > b is the same block.

    Args:
        a: The first value.
        b: The second value.
    """
    ...

def less(a: Value, b: Value) -> bool:
    """True when a is less than b. a < b is the same block.

    Args:
        a: The first value.
        b: The second value.
    """
    ...

def equal(a: Value, b: Value) -> bool:
    """True when a equals b. a == b is the same block.

    Args:
        a: The first value.
        b: The second value.
    """
    ...

def both(a: bool, b: bool) -> bool:
    """True when both conditions are true. a and b is the same block.

    Args:
        a: The first condition.
        b: The second condition.
    """
    ...

def either(a: bool, b: bool) -> bool:
    """True when either condition is true. a or b is the same block.

    Args:
        a: The first condition.
        b: The second condition.
    """
    ...

def not_(value: bool) -> bool:
    """True when the condition is false. not value is the same block.

    Args:
        value: The condition to flip.
    """
    ...

def join(a: Value, b: Value) -> Value:
    """Join two values into text. a + b on text is the same block.

    Args:
        a: The first value.
        b: The second value.
    """
    ...

def letter(index: Value, text: Value) -> Value:
    """One letter of a text. This Scratch block starts at 1. text[0] is the first letter.

    Args:
        index: Which letter. 1 is the first letter of this block.
        text: The text to read.
    """
    ...

def mod(a: Value, b: Value) -> Number:
    """The remainder of a divided by b. a % b is the same block.

    Args:
        a: The number to divide.
        b: The number to divide by.
    """
    ...

def round(n: Value) -> Number:
    """Round to the nearest whole number. round(n) is the same block.

    Args:
        n: The number to round.
    """
    ...

def set(variable: Any, value: Value) -> None:
    """Set a variable. score = value is the same block.

    Args:
        variable: The variable.
        value: The new value.
    """
    ...

def change(variable: Any, value: Value) -> None:
    """Change a variable by a number. score += value is the same block.

    Args:
        variable: The variable.
        value: How much to add. Use a negative number to subtract.
    """
    ...

def show_variable(variable: Any) -> None:
    """Show a variable's monitor.

    Args:
        variable: The variable.
    """
    ...

def hide_variable(variable: Any) -> None:
    """Hide a variable's monitor.

    Args:
        variable: The variable.
    """
    ...

def add(item: Value, list: Any) -> None:
    """Add an item to a list. items.append(item) is the same block. This is not number addition.

    Args:
        item: The item to add.
        list: The list.
    """
    ...

def delete(index: Index, list: Any) -> None:
    """Delete an item from a one-dimensional list.

    Args:
        index: The position, starting at 1, or "last", "all", or "random".
        list: The list.
    """
    ...

def delete_all(list: Any) -> None:
    """Delete every item in a one-dimensional list. items.clear() is the same block.

    Args:
        list: The list.
    """
    ...

def insert(item: Value, index: Index, list: Any) -> None:
    """Insert an item into a one-dimensional list. items.insert(index, item) is the same idea.

    Args:
        item: The item to insert.
        index: The position, starting at 1, or "last" or "random".
        list: The list.
    """
    ...

def replace(index: Index, list: Any, item: Value) -> None:
    """Replace an item in a one-dimensional list. items[index] = item is the same block.

    Args:
        index: The position, starting at 1, or "last" or "random".
        list: The list.
        item: The new item.
    """
    ...

def item_of(index: Index, list: Any) -> Value:
    """Read an item from a list. items[index] is the same block.

    Args:
        index: The position, starting at 1, or "last" or "random".
        list: The list.
    """
    ...

def item_number(item: Value, list: Any) -> Number:
    """Where an item first appears. Positions start at 1. items.index(item) is the same block.

    Args:
        item: The item to find.
        list: The list.
    """
    ...

def show_list(list: Any) -> None:
    """Show a list's monitor.

    Args:
        list: The list.
    """
    ...

def hide_list(list: Any) -> None:
    """Hide a list's monitor.

    Args:
        list: The list.
    """
    ...

def broadcast(message: str) -> None:
    """Send a message.

    Args:
        message: The message name.
    """
    ...

def broadcast_and_wait(message: str) -> None:
    """Send a message and wait for every receiver to finish.

    Args:
        message: The message name.
    """
    ...

def erase_all() -> None:
    """Erase all pen marks. Turns on the Pen extension."""
    ...

def stamp() -> None:
    """Stamp the sprite's image onto the stage."""
    ...

def pen_down() -> None:
    """Put the pen down."""
    ...

def pen_up() -> None:
    """Pick the pen up."""
    ...

def set_pen_color(color: str) -> None:
    """Set the pen color.

    Args:
        color: A color written "#rrggbb", such as "#ff0000".
    """
    ...

def change_pen_color(amount: Value) -> None:
    """Change the pen color by a number.

    Args:
        amount: How much to add to the color.
    """
    ...

def set_pen_size(size: Value) -> None:
    """Set the pen size.

    Args:
        size: The pen size.
    """
    ...

def change_pen_size(amount: Value) -> None:
    """Change the pen size.

    Args:
        amount: How much to add.
    """
    ...

def set_pen(param: PenParam, value: Value) -> None:
    """Set one pen parameter.

    Args:
        param: "color", "saturation", "brightness", or "transparency".
        value: The new amount.
    """
    ...

def change_pen(param: PenParam, value: Value) -> None:
    """Change one pen parameter.

    Args:
        param: "color", "saturation", "brightness", or "transparency".
        value: How much to add.
    """
    ...

def abs(n: Value) -> Number:
    """Absolute value. abs(n) and math.fabs(n) are the same block.

    Args:
        n: The number.
    """
    ...

def floor(n: Value) -> Number:
    """Round down. math.floor(n) is the same block.

    Args:
        n: The number.
    """
    ...

def ceiling(n: Value) -> Number:
    """Round up. math.ceil(n) is the same block.

    Args:
        n: The number.
    """
    ...

def sqrt(n: Value) -> Number:
    """Square root. math.sqrt(n) is the same block.

    Args:
        n: The number.
    """
    ...

def sin(n: Value) -> Number:
    """Sine of an angle in degrees. math.sin uses radians.

    Args:
        n: The angle in degrees.
    """
    ...

def cos(n: Value) -> Number:
    """Cosine of an angle in degrees. math.cos uses radians.

    Args:
        n: The angle in degrees.
    """
    ...

def tan(n: Value) -> Number:
    """Tangent of an angle in degrees. math.tan uses radians.

    Args:
        n: The angle in degrees.
    """
    ...

def asin(n: Value) -> Number:
    """Arcsine in degrees. math.asin returns radians.

    Args:
        n: The sine of the angle.
    """
    ...

def acos(n: Value) -> Number:
    """Arccosine in degrees. math.acos returns radians.

    Args:
        n: The cosine of the angle.
    """
    ...

def atan(n: Value) -> Number:
    """Arctangent in degrees. math.atan returns radians.

    Args:
        n: The tangent of the angle.
    """
    ...

def ln(n: Value) -> Number:
    """Natural log. math.log(n) is the same block.

    Args:
        n: The number.
    """
    ...

def log(n: Value) -> Number:
    """Log base 10. math.log10(n) is the same block.

    Args:
        n: The number.
    """
    ...

def exp(n: Value) -> Number:
    """e raised to a power. math.exp(n) is the same block.

    Args:
        n: The exponent.
    """
    ...

def power10(n: Value) -> Number:
    """10 raised to a power.

    Args:
        n: The exponent.
    """
    ...

def math(op: MathOp, n: Value) -> Number:
    """A Scratch math block chosen by name. Prefer math.sin and the other math functions.

    Args:
        op: "abs", "floor", "ceiling", "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "e ^", or "10 ^".
        n: The number.
    """
    ...

def length(value: Any) -> Number:
    """Length of a list, dictionary, or text. len(value) is the same block.

    Args:
        value: A list, a dictionary, or text.
    """
    ...

def contains(container: Any, item: Value) -> bool:
    """True when a list or dictionary contains a value. item in items is the same block.

    Args:
        container: The list or dictionary.
        item: The value to look for.
    """
    ...

def variable(name: str, value: Value = 0, *, shared: bool = False, show: bool = False) -> Any:
    """Declare a variable when you want a Scratch name, a monitor, or a shared value.

    Args:
        name: The Scratch name.
        value: The starting value.
        shared: True puts the variable on the stage, so every sprite can see it.
        show: True shows the monitor.
    """
    ...

def list(name: str, value: Any = None, *, shared: bool = False, show: bool = False) -> Any:
    """Declare a list when you want a Scratch name, a monitor, or a shared list.

    Args:
        name: The Scratch name.
        value: The starting items. Omit it for an empty list.
        shared: True puts the list on the stage.
        show: True shows the monitor.
    """
    ...

def dict(name: str, value: Any = None, *, shared: bool = False, show: bool = False) -> Any:
    """Declare a dictionary as a keys list and a values list.

    Args:
        name: The Scratch name. The lists are called name keys and name values.
        value: The starting pairs, such as {'ada': 3}. Omit it for an empty dictionary.
        shared: True puts both lists on the stage.
        show: True shows both monitors.
    """
    ...

def costume(path: str, *, name: str | None = None) -> None:
    """Add a costume file to this sprite. svg, png, and jpg work.

    Args:
        path: The file path, relative to the script.
        name: The Scratch name. Omit it to use the file name.
    """
    ...

def sound(path: str, *, name: str | None = None) -> None:
    """Add a sound file to this sprite. Sounds are usually wav.

    Args:
        path: The file path, relative to the script.
        name: The Scratch name. Omit it to use the file name.
    """
    ...

def backdrop(path: str, *, name: str | None = None) -> None:
    """Add a backdrop file to the stage.

    Args:
        path: The file path, relative to the script.
        name: The Scratch name. Omit it to use the file name.
    """
    ...

def sprite_name(name: str) -> None:
    """Set this sprite's name.

    Args:
        name: The name Scratch shows.
    """
    ...


class Sprite:
    """A Scratch sprite.

    Subclass it, store state on self, and call Scratch blocks as methods.
    Each instance you create becomes its own sprite.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Arguments are numbers, text, or lists. Each instance is baked into the project."""
        ...

    def clone(self) -> None:
        """Create a clone of this sprite."""
        ...

    def move(self, steps: Value) -> None:
        """Move the sprite by a number of steps.

        Args:
            steps: How many steps to move.
        """
        ...

    def turn_right(self, degrees: Value) -> None:
        """Turn the sprite to the right.

        Args:
            degrees: How many degrees to turn.
        """
        ...

    def turn_left(self, degrees: Value) -> None:
        """Turn the sprite to the left.

        Args:
            degrees: How many degrees to turn.
        """
        ...

    def go_to(self, target: GoTarget) -> None:
        """Go to a sprite, the mouse, or a random position.

        Args:
            target: "mouse-pointer", "random position", or a sprite name.
        """
        ...

    def go_to_xy(self, x: Value, y: Value) -> None:
        """Go to an x and y position.

        Args:
            x: The x position.
            y: The y position.
        """
        ...

    def glide_to(self, seconds: Value, target: GoTarget) -> None:
        """Glide to a sprite, the mouse, or a random position.

        Args:
            seconds: How long the glide takes.
            target: "mouse-pointer", "random position", or a sprite name.
        """
        ...

    def glide_to_xy(self, seconds: Value, x: Value, y: Value) -> None:
        """Glide to an x and y position.

        Args:
            seconds: How long the glide takes.
            x: The x position.
            y: The y position.
        """
        ...

    def point_in_direction(self, direction: Value) -> None:
        """Point the sprite in a direction. 90 is right.

        Args:
            direction: The direction in degrees.
        """
        ...

    def point_towards(self, target: PointTarget) -> None:
        """Point towards the mouse or a sprite.

        Args:
            target: "mouse-pointer" or a sprite name.
        """
        ...

    def change_x(self, dx: Value) -> None:
        """Change x by a number.

        Args:
            dx: How much to add to x.
        """
        ...

    def set_x(self, x: Value) -> None:
        """Set x to a number.

        Args:
            x: The new x position.
        """
        ...

    def change_y(self, dy: Value) -> None:
        """Change y by a number.

        Args:
            dy: How much to add to y.
        """
        ...

    def set_y(self, y: Value) -> None:
        """Set y to a number.

        Args:
            y: The new y position.
        """
        ...

    def if_on_edge_bounce(self) -> None:
        """If the sprite is on the edge, bounce."""
        ...

    def set_rotation_style(self, style: RotationStyle) -> None:
        """Set how the sprite rotates.

        Args:
            style: "left-right", "all around", or "don't rotate".
        """
        ...

    def x_position(self) -> Number:
        """Return the sprite's x position."""
        ...

    def y_position(self) -> Number:
        """Return the sprite's y position."""
        ...

    def direction(self) -> Number:
        """Return the sprite's direction."""
        ...

    def say(self, message: Value) -> None:
        """Say a message in a speech bubble.

        Args:
            message: Text or a number to show.
        """
        ...

    def say_for(self, message: Value, seconds: Value) -> None:
        """Say a message, then clear it.

        Args:
            message: Text or a number to show.
            seconds: How long the bubble stays.
        """
        ...

    def think(self, message: Value) -> None:
        """Think a message in a thought bubble.

        Args:
            message: Text or a number to show.
        """
        ...

    def think_for(self, message: Value, seconds: Value) -> None:
        """Think a message, then clear it.

        Args:
            message: Text or a number to show.
            seconds: How long the bubble stays.
        """
        ...

    def switch_costume(self, costume: str) -> None:
        """Switch to a costume on this sprite.

        Args:
            costume: The costume's name.
        """
        ...

    def next_costume(self) -> None:
        """Switch to the next costume."""
        ...

    def switch_backdrop(self, backdrop: str) -> None:
        """Switch the stage backdrop.

        Args:
            backdrop: The backdrop's name.
        """
        ...

    def switch_backdrop_and_wait(self, backdrop: str) -> None:
        """Switch the backdrop and wait for other scripts that start because of it.

        Args:
            backdrop: The backdrop's name.
        """
        ...

    def next_backdrop(self) -> None:
        """Switch to the next backdrop."""
        ...

    def change_size(self, change: Value) -> None:
        """Change the sprite's size.

        Args:
            change: How much to add to the size.
        """
        ...

    def set_size(self, size: Value) -> None:
        """Set the sprite's size. 100 is normal.

        Args:
            size: The size, as a percent.
        """
        ...

    def change_effect(self, effect: Effect, change: Value) -> None:
        """Change a graphic effect.

        Args:
            effect: "color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", or "ghost".
            change: How much to add.
        """
        ...

    def set_effect(self, effect: Effect, value: Value) -> None:
        """Set a graphic effect.

        Args:
            effect: "color", "fisheye", "whirl", "pixelate", "mosaic", "brightness", or "ghost".
            value: The new amount.
        """
        ...

    def clear_graphic_effects(self) -> None:
        """Clear every graphic effect."""
        ...

    def show(self) -> None:
        """Show the sprite."""
        ...

    def hide(self) -> None:
        """Hide the sprite."""
        ...

    def go_to_layer(self, layer: Layer) -> None:
        """Go to the front or back layer.

        Args:
            layer: "front" or "back".
        """
        ...

    def go_layers(self, direction: LayerDirection, number: Value) -> None:
        """Move forward or backward a number of layers.

        Args:
            direction: "forward" or "backward".
            number: How many layers to move.
        """
        ...

    def costume_number(self) -> Number:
        """Return the costume number."""
        ...

    def costume_name(self) -> Value:
        """Return the costume name."""
        ...

    def backdrop_number(self) -> Number:
        """Return the backdrop number."""
        ...

    def backdrop_name(self) -> Value:
        """Return the backdrop name."""
        ...

    def size(self) -> Number:
        """Return the sprite's size."""
        ...

    def play_until_done(self, sound: str) -> None:
        """Play a sound and wait until it finishes.

        Args:
            sound: The sound's name.
        """
        ...

    def start_sound(self, sound: str) -> None:
        """Start a sound without waiting.

        Args:
            sound: The sound's name.
        """
        ...

    def stop_all_sounds(self) -> None:
        """Stop every sound."""
        ...

    def change_sound_effect(self, effect: SoundEffect, value: Value) -> None:
        """Change a sound effect.

        Args:
            effect: "pitch" or "pan left/right".
            value: How much to add.
        """
        ...

    def set_sound_effect(self, effect: SoundEffect, value: Value) -> None:
        """Set a sound effect.

        Args:
            effect: "pitch" or "pan left/right".
            value: The new amount.
        """
        ...

    def clear_sound_effects(self) -> None:
        """Clear every sound effect."""
        ...

    def change_volume(self, amount: Value) -> None:
        """Change the volume.

        Args:
            amount: How much to add.
        """
        ...

    def set_volume(self, percent: Value) -> None:
        """Set the volume. 100 is full.

        Args:
            percent: The volume, as a percent.
        """
        ...

    def volume(self) -> Number:
        """Return the volume."""
        ...

    def wait(self, seconds: Value) -> None:
        """Wait a number of seconds.

        Args:
            seconds: How long to wait.
        """
        ...

    def repeat(self, times: Value) -> _With:
        """Repeat the with-block a number of times. for _ in range(n) is the same block.

        Args:
            times: How many times to repeat.
        """
        ...

    def forever(self) -> _With:
        """Repeat the with-block forever. while True is the same block."""
        ...

    def if_(self, condition: bool) -> _With:
        """Run the with-block when the condition is true. A Python if can also have elif and else.

        Args:
            condition: A comparison, touching, or other boolean block.
        """
        ...

    def repeat_until(self, condition: bool) -> _With:
        """Repeat the with-block until the condition is true.

        Args:
            condition: A comparison, touching, or other boolean block.
        """
        ...

    def wait_until(self, condition: bool) -> None:
        """Wait until the condition is true.

        Args:
            condition: A comparison, touching, or other boolean block.
        """
        ...

    def stop(self, what: StopOption) -> None:
        """Stop scripts.

        Args:
            what: "all", "this script", or "other scripts".
        """
        ...

    def create_clone(self, target: CloneTarget = "myself") -> None:
        """Create a clone of this sprite or another sprite.

        Args:
            target: "myself" or a sprite name.
        """
        ...

    def delete_clone(self) -> None:
        """Delete this clone."""
        ...

    def touching(self, target: TouchTarget) -> bool:
        """True when the sprite touches a target.

        Args:
            target: "mouse-pointer", "edge", or a sprite name.
        """
        ...

    def touching_color(self, color: str) -> bool:
        """True when the sprite touches a color.

        Args:
            color: A color written "#rrggbb", such as "#ff0000".
        """
        ...

    def color_is_touching(self, color: str, color2: str) -> bool:
        """True when one color on this sprite touches another color.

        Args:
            color: The color on this sprite, "#rrggbb".
            color2: The other color, "#rrggbb".
        """
        ...

    def distance_to(self, target: DistanceTarget) -> Number:
        """Distance to the mouse or a sprite.

        Args:
            target: "mouse-pointer" or a sprite name.
        """
        ...

    def ask(self, question: Value) -> None:
        """Ask a question and wait. The reply is kitty.answer().

        Args:
            question: The question to ask.
        """
        ...

    def answer(self) -> Value:
        """The reply from the last ask."""
        ...

    def key_pressed(self, key: Key) -> bool:
        """True while a key is pressed.

        Args:
            key: "space", "up arrow", "down arrow", "left arrow", "right arrow", "enter", "any", or a letter or digit. "up", "down", "left", and "right" are the arrow keys.
        """
        ...

    def mouse_down(self) -> bool:
        """True while the mouse button is down."""
        ...

    def mouse_x(self) -> Number:
        """The mouse x position."""
        ...

    def mouse_y(self) -> Number:
        """The mouse y position."""
        ...

    def set_drag_mode(self, mode: DragMode) -> None:
        """Let the viewer drag this sprite, or not.

        Args:
            mode: "draggable" or "not draggable".
        """
        ...

    def loudness(self) -> Number:
        """How loud the microphone is."""
        ...

    def timer(self) -> Number:
        """Seconds since the timer was reset."""
        ...

    def reset_timer(self) -> None:
        """Reset the timer."""
        ...

    def property_of(self, property: Property, target: ObjectTarget) -> Value:
        """Read a property of a sprite or the stage.

        Args:
            property: "x position", "y position", "direction", "costume #", "costume name", "size", "volume", "backdrop #", or "backdrop name".
            target: A sprite name, or "stage".
        """
        ...

    def current(self, unit: TimeUnit) -> Number:
        """The current year, month, date, day of the week, hour, minute, or second.

        Args:
            unit: "year", "month", "date", "day of week", "hour", "minute", or "second".
        """
        ...

    def days_since_2000(self) -> Number:
        """Days since 2000."""
        ...

    def username(self) -> Value:
        """The Scratch username of the viewer."""
        ...

    def subtract(self, a: Value, b: Value) -> Number:
        """Subtract two numbers. a - b is the same block.

        Args:
            a: The number to subtract from.
            b: The number to subtract.
        """
        ...

    def multiply(self, a: Value, b: Value) -> Number:
        """Multiply two numbers. a * b is the same block.

        Args:
            a: The first number.
            b: The second number.
        """
        ...

    def divide(self, a: Value, b: Value) -> Number:
        """Divide two numbers. a / b is the same block.

        Args:
            a: The number to divide.
            b: The number to divide by.
        """
        ...

    def random(self, start: Value, end: Value) -> Number:
        """Pick a random number from start through end.

        Args:
            start: The low end.
            end: The high end.
        """
        ...

    def greater(self, a: Value, b: Value) -> bool:
        """True when a is greater than b. a > b is the same block.

        Args:
            a: The first value.
            b: The second value.
        """
        ...

    def less(self, a: Value, b: Value) -> bool:
        """True when a is less than b. a < b is the same block.

        Args:
            a: The first value.
            b: The second value.
        """
        ...

    def equal(self, a: Value, b: Value) -> bool:
        """True when a equals b. a == b is the same block.

        Args:
            a: The first value.
            b: The second value.
        """
        ...

    def both(self, a: bool, b: bool) -> bool:
        """True when both conditions are true. a and b is the same block.

        Args:
            a: The first condition.
            b: The second condition.
        """
        ...

    def either(self, a: bool, b: bool) -> bool:
        """True when either condition is true. a or b is the same block.

        Args:
            a: The first condition.
            b: The second condition.
        """
        ...

    def not_(self, value: bool) -> bool:
        """True when the condition is false. not value is the same block.

        Args:
            value: The condition to flip.
        """
        ...

    def join(self, a: Value, b: Value) -> Value:
        """Join two values into text. a + b on text is the same block.

        Args:
            a: The first value.
            b: The second value.
        """
        ...

    def letter(self, index: Value, text: Value) -> Value:
        """One letter of a text. This Scratch block starts at 1. text[0] is the first letter.

        Args:
            index: Which letter. 1 is the first letter of this block.
            text: The text to read.
        """
        ...

    def mod(self, a: Value, b: Value) -> Number:
        """The remainder of a divided by b. a % b is the same block.

        Args:
            a: The number to divide.
            b: The number to divide by.
        """
        ...

    def round(self, n: Value) -> Number:
        """Round to the nearest whole number. round(n) is the same block.

        Args:
            n: The number to round.
        """
        ...

    def set(self, variable: Any, value: Value) -> None:
        """Set a variable. score = value is the same block.

        Args:
            variable: The variable.
            value: The new value.
        """
        ...

    def change(self, variable: Any, value: Value) -> None:
        """Change a variable by a number. score += value is the same block.

        Args:
            variable: The variable.
            value: How much to add. Use a negative number to subtract.
        """
        ...

    def show_variable(self, variable: Any) -> None:
        """Show a variable's monitor.

        Args:
            variable: The variable.
        """
        ...

    def hide_variable(self, variable: Any) -> None:
        """Hide a variable's monitor.

        Args:
            variable: The variable.
        """
        ...

    def add(self, item: Value, list: Any) -> None:
        """Add an item to a list. items.append(item) is the same block. This is not number addition.

        Args:
            item: The item to add.
            list: The list.
        """
        ...

    def delete(self, index: Index, list: Any) -> None:
        """Delete an item from a one-dimensional list.

        Args:
            index: The position, starting at 1, or "last", "all", or "random".
            list: The list.
        """
        ...

    def delete_all(self, list: Any) -> None:
        """Delete every item in a one-dimensional list. items.clear() is the same block.

        Args:
            list: The list.
        """
        ...

    def insert(self, item: Value, index: Index, list: Any) -> None:
        """Insert an item into a one-dimensional list. items.insert(index, item) is the same idea.

        Args:
            item: The item to insert.
            index: The position, starting at 1, or "last" or "random".
            list: The list.
        """
        ...

    def replace(self, index: Index, list: Any, item: Value) -> None:
        """Replace an item in a one-dimensional list. items[index] = item is the same block.

        Args:
            index: The position, starting at 1, or "last" or "random".
            list: The list.
            item: The new item.
        """
        ...

    def item_of(self, index: Index, list: Any) -> Value:
        """Read an item from a list. items[index] is the same block.

        Args:
            index: The position, starting at 1, or "last" or "random".
            list: The list.
        """
        ...

    def item_number(self, item: Value, list: Any) -> Number:
        """Where an item first appears. Positions start at 1. items.index(item) is the same block.

        Args:
            item: The item to find.
            list: The list.
        """
        ...

    def show_list(self, list: Any) -> None:
        """Show a list's monitor.

        Args:
            list: The list.
        """
        ...

    def hide_list(self, list: Any) -> None:
        """Hide a list's monitor.

        Args:
            list: The list.
        """
        ...

    def broadcast(self, message: str) -> None:
        """Send a message.

        Args:
            message: The message name.
        """
        ...

    def broadcast_and_wait(self, message: str) -> None:
        """Send a message and wait for every receiver to finish.

        Args:
            message: The message name.
        """
        ...

    def erase_all(self) -> None:
        """Erase all pen marks. Turns on the Pen extension."""
        ...

    def stamp(self) -> None:
        """Stamp the sprite's image onto the stage."""
        ...

    def pen_down(self) -> None:
        """Put the pen down."""
        ...

    def pen_up(self) -> None:
        """Pick the pen up."""
        ...

    def set_pen_color(self, color: str) -> None:
        """Set the pen color.

        Args:
            color: A color written "#rrggbb", such as "#ff0000".
        """
        ...

    def change_pen_color(self, amount: Value) -> None:
        """Change the pen color by a number.

        Args:
            amount: How much to add to the color.
        """
        ...

    def set_pen_size(self, size: Value) -> None:
        """Set the pen size.

        Args:
            size: The pen size.
        """
        ...

    def change_pen_size(self, amount: Value) -> None:
        """Change the pen size.

        Args:
            amount: How much to add.
        """
        ...

    def set_pen(self, param: PenParam, value: Value) -> None:
        """Set one pen parameter.

        Args:
            param: "color", "saturation", "brightness", or "transparency".
            value: The new amount.
        """
        ...

    def change_pen(self, param: PenParam, value: Value) -> None:
        """Change one pen parameter.

        Args:
            param: "color", "saturation", "brightness", or "transparency".
            value: How much to add.
        """
        ...

    def abs(self, n: Value) -> Number:
        """Absolute value. abs(n) and math.fabs(n) are the same block.

        Args:
            n: The number.
        """
        ...

    def floor(self, n: Value) -> Number:
        """Round down. math.floor(n) is the same block.

        Args:
            n: The number.
        """
        ...

    def ceiling(self, n: Value) -> Number:
        """Round up. math.ceil(n) is the same block.

        Args:
            n: The number.
        """
        ...

    def sqrt(self, n: Value) -> Number:
        """Square root. math.sqrt(n) is the same block.

        Args:
            n: The number.
        """
        ...

    def sin(self, n: Value) -> Number:
        """Sine of an angle in degrees. math.sin uses radians.

        Args:
            n: The angle in degrees.
        """
        ...

    def cos(self, n: Value) -> Number:
        """Cosine of an angle in degrees. math.cos uses radians.

        Args:
            n: The angle in degrees.
        """
        ...

    def tan(self, n: Value) -> Number:
        """Tangent of an angle in degrees. math.tan uses radians.

        Args:
            n: The angle in degrees.
        """
        ...

    def asin(self, n: Value) -> Number:
        """Arcsine in degrees. math.asin returns radians.

        Args:
            n: The sine of the angle.
        """
        ...

    def acos(self, n: Value) -> Number:
        """Arccosine in degrees. math.acos returns radians.

        Args:
            n: The cosine of the angle.
        """
        ...

    def atan(self, n: Value) -> Number:
        """Arctangent in degrees. math.atan returns radians.

        Args:
            n: The tangent of the angle.
        """
        ...

    def ln(self, n: Value) -> Number:
        """Natural log. math.log(n) is the same block.

        Args:
            n: The number.
        """
        ...

    def log(self, n: Value) -> Number:
        """Log base 10. math.log10(n) is the same block.

        Args:
            n: The number.
        """
        ...

    def exp(self, n: Value) -> Number:
        """e raised to a power. math.exp(n) is the same block.

        Args:
            n: The exponent.
        """
        ...

    def power10(self, n: Value) -> Number:
        """10 raised to a power.

        Args:
            n: The exponent.
        """
        ...


class Stage(Sprite):
    """The Scratch stage. Subclass it for backdrop scripts."""
    ...


class _Required:
    """Marks a block input that the script must provide."""


REQUIRED: _Required


class Spec:
    opcode: str
    shape: str
    params: tuple[Any, ...]
    doc: str
    extension: str | None
    fixed_fields: tuple[Any, ...]

    def __init__(self, opcode: str, shape: str, params: Any, doc: str, extension: str | None = ..., fixed_fields: Any = ...) -> None: ...
    def python_signature(self) -> Signature: ...


BLOCKS: dict[str, Spec]
MENUS: dict[str, tuple[str, str]]
DECLARATIONS: set[str]
MATH: dict[str, str]
