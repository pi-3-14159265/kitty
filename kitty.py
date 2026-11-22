"""Scratch blocks for Python scripts compiled with comp.py.

Scripts are not run by Python. Compile them:

    python comp.py script.py
    python comp.py stage.py cat.py -o game.sb3

A call such as kitty.say("Hello world!") becomes the Scratch block
say [Hello world!]. Statements at the top of a file run when the green
flag is clicked.

Classes are sprites. self.score is a variable on that sprite, and
self.say(...) is the same block as kitty.say(...).

    import kitty

    class Cat(kitty.Sprite):
        def __init__(self):
            self.score = 0

        @kitty.green_flag
        def start(self):
            self.say("Hello world!")
            self.move(10)

    score = 0

    kitty.say("Hello world!")
    kitty.move(10)
    with kitty.repeat(10):
        if kitty.touching("mouse-pointer"):
            kitty.say(score)
"""

from __future__ import annotations

from inspect import Parameter, Signature


class _Required:
    """Marks a block input that the script must provide."""


REQUIRED = _Required()


class Spec:
    def __init__(self, opcode, shape, params, doc, extension=None, fixed_fields=()):
        self.opcode = opcode
        self.shape = shape
        self.params = tuple(params)
        self.doc = doc
        self.extension = extension
        self.fixed_fields = tuple(fixed_fields)

    def python_signature(self):
        parameters = []
        for param in self.params:
            name, _scratch, _slot, *rest = param
            default = rest[0] if rest else REQUIRED
            if default is REQUIRED:
                parameters.append(Parameter(name, Parameter.POSITIONAL_OR_KEYWORD))
            else:
                parameters.append(
                    Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=default)
                )
        return Signature(parameters)


def _param(name, scratch, slot, default=REQUIRED):
    if default is REQUIRED:
        return (name, scratch, slot)
    return (name, scratch, slot, default)


def _spec(opcode, shape, params, doc, extension=None, fixed_fields=()):
    return Spec(opcode, shape, params, doc, extension, fixed_fields)


def _compile_only(*_args, **_kwargs):
    raise RuntimeError(
        "kitty scripts are compiled into Scratch. Run: python comp.py your_script.py"
    )


# shape is stack, reporter, boolean, or c (a C-shaped block used with `with`).
BLOCKS = {
    # Motion
    "move": _spec("motion_movesteps", "stack", [_param("steps", "STEPS", "number")], "move (steps) steps"),
    "turn_right": _spec("motion_turnright", "stack", [_param("degrees", "DEGREES", "number")], "turn right (degrees) degrees"),
    "turn_left": _spec("motion_turnleft", "stack", [_param("degrees", "DEGREES", "number")], "turn left (degrees) degrees"),
    "go_to": _spec("motion_goto", "stack", [_param("target", "TO", "menu:goto")], "go to [target]"),
    "go_to_xy": _spec("motion_gotoxy", "stack", [_param("x", "X", "number"), _param("y", "Y", "number")], "go to x: (x) y: (y)"),
    "glide_to": _spec("motion_glideto", "stack", [_param("seconds", "SECS", "number"), _param("target", "TO", "menu:glide")], "glide (seconds) secs to [target]"),
    "glide_to_xy": _spec("motion_glidesecstoxy", "stack", [_param("seconds", "SECS", "number"), _param("x", "X", "number"), _param("y", "Y", "number")], "glide (seconds) secs to x: (x) y: (y)"),
    "point_in_direction": _spec("motion_pointindirection", "stack", [_param("direction", "DIRECTION", "angle")], "point in direction (direction)"),
    "point_towards": _spec("motion_pointtowards", "stack", [_param("target", "TOWARDS", "menu:point")], "point towards [target]"),
    "change_x": _spec("motion_changexby", "stack", [_param("dx", "DX", "number")], "change x by (dx)"),
    "set_x": _spec("motion_setx", "stack", [_param("x", "X", "number")], "set x to (x)"),
    "change_y": _spec("motion_changeyby", "stack", [_param("dy", "DY", "number")], "change y by (dy)"),
    "set_y": _spec("motion_sety", "stack", [_param("y", "Y", "number")], "set y to (y)"),
    "if_on_edge_bounce": _spec("motion_ifonedgebounce", "stack", [], "if on edge, bounce"),
    "set_rotation_style": _spec("motion_setrotationstyle", "stack", [_param("style", "STYLE", "field:rotation")], "set rotation style [style]"),
    "x_position": _spec("motion_xposition", "reporter", [], "(x position)"),
    "y_position": _spec("motion_yposition", "reporter", [], "(y position)"),
    "direction": _spec("motion_direction", "reporter", [], "(direction)"),
    # Looks
    "say": _spec("looks_say", "stack", [_param("message", "MESSAGE", "text")], "say [message]"),
    "say_for": _spec("looks_sayforsecs", "stack", [_param("message", "MESSAGE", "text"), _param("seconds", "SECS", "number")], "say [message] for (seconds) seconds"),
    "think": _spec("looks_think", "stack", [_param("message", "MESSAGE", "text")], "think [message]"),
    "think_for": _spec("looks_thinkforsecs", "stack", [_param("message", "MESSAGE", "text"), _param("seconds", "SECS", "number")], "think [message] for (seconds) seconds"),
    "switch_costume": _spec("looks_switchcostumeto", "stack", [_param("costume", "COSTUME", "menu:costume")], "switch costume to [costume]"),
    "next_costume": _spec("looks_nextcostume", "stack", [], "next costume"),
    "switch_backdrop": _spec("looks_switchbackdropto", "stack", [_param("backdrop", "BACKDROP", "menu:backdrop")], "switch backdrop to [backdrop]"),
    "switch_backdrop_and_wait": _spec("looks_switchbackdroptoandwait", "stack", [_param("backdrop", "BACKDROP", "menu:backdrop")], "switch backdrop to [backdrop] and wait"),
    "next_backdrop": _spec("looks_nextbackdrop", "stack", [], "next backdrop"),
    "change_size": _spec("looks_changesizeby", "stack", [_param("change", "CHANGE", "number")], "change size by (change)"),
    "set_size": _spec("looks_setsizeto", "stack", [_param("size", "SIZE", "number")], "set size to (size) %"),
    "change_effect": _spec("looks_changeeffectby", "stack", [_param("effect", "EFFECT", "field:effect"), _param("change", "CHANGE", "number")], "change [effect] effect by (change)"),
    "set_effect": _spec("looks_seteffectto", "stack", [_param("effect", "EFFECT", "field:effect"), _param("value", "VALUE", "number")], "set [effect] effect to (value)"),
    "clear_graphic_effects": _spec("looks_cleargraphiceffects", "stack", [], "clear graphic effects"),
    "show": _spec("looks_show", "stack", [], "show"),
    "hide": _spec("looks_hide", "stack", [], "hide"),
    "go_to_layer": _spec("looks_gotofrontback", "stack", [_param("layer", "FRONT_BACK", "field:front")], "go to [layer] layer"),
    "go_layers": _spec("looks_goforwardbackwardlayers", "stack", [_param("direction", "FORWARD_BACKWARD", "field:layers"), _param("number", "NUM", "integer")], "go [direction] (number) layers"),
    "costume_number": _spec("looks_costumenumbername", "reporter", [], "(costume [number])", fixed_fields=(("NUMBER_NAME", "number"),)),
    "costume_name": _spec("looks_costumenumbername", "reporter", [], "(costume [name])", fixed_fields=(("NUMBER_NAME", "name"),)),
    "backdrop_number": _spec("looks_backdropnumbername", "reporter", [], "(backdrop [number])", fixed_fields=(("NUMBER_NAME", "number"),)),
    "backdrop_name": _spec("looks_backdropnumbername", "reporter", [], "(backdrop [name])", fixed_fields=(("NUMBER_NAME", "name"),)),
    "size": _spec("looks_size", "reporter", [], "(size)"),
    # Sound
    "play_until_done": _spec("sound_playuntildone", "stack", [_param("sound", "SOUND_MENU", "menu:sound")], "play sound [sound] until done"),
    "start_sound": _spec("sound_play", "stack", [_param("sound", "SOUND_MENU", "menu:sound")], "start sound [sound]"),
    "stop_all_sounds": _spec("sound_stopallsounds", "stack", [], "stop all sounds"),
    "change_sound_effect": _spec("sound_changeeffectby", "stack", [_param("effect", "EFFECT", "field:sound_effect"), _param("value", "VALUE", "number")], "change [effect] effect by (value)"),
    "set_sound_effect": _spec("sound_seteffectto", "stack", [_param("effect", "EFFECT", "field:sound_effect"), _param("value", "VALUE", "number")], "set [effect] effect to (value)"),
    "clear_sound_effects": _spec("sound_cleareffects", "stack", [], "clear sound effects"),
    "change_volume": _spec("sound_changevolumeby", "stack", [_param("amount", "VOLUME", "number")], "change volume by (amount)"),
    "set_volume": _spec("sound_setvolumeto", "stack", [_param("percent", "VOLUME", "number")], "set volume to (percent) %"),
    "volume": _spec("sound_volume", "reporter", [], "(volume)"),
    # Control
    "wait": _spec("control_wait", "stack", [_param("seconds", "DURATION", "positive")], "wait (seconds) seconds"),
    "repeat": _spec("control_repeat", "c", [_param("times", "TIMES", "whole")], "repeat (times)"),
    "forever": _spec("control_forever", "c", [], "forever"),
    "if_": _spec("control_if", "c", [_param("condition", "CONDITION", "boolean")], "if <condition> then"),
    "repeat_until": _spec("control_repeat_until", "c", [_param("condition", "CONDITION", "boolean")], "repeat until <condition>"),
    "wait_until": _spec("control_wait_until", "stack", [_param("condition", "CONDITION", "boolean")], "wait until <condition>"),
    "stop": _spec("control_stop", "stack", [_param("what", "STOP_OPTION", "field:stop")], "stop [what]"),
    "create_clone": _spec("control_create_clone_of", "stack", [_param("target", "CLONE_OPTION", "menu:clone", "myself")], "create clone of [target]"),
    "delete_clone": _spec("control_delete_this_clone", "stack", [], "delete this clone"),
    # Sensing
    "touching": _spec("sensing_touchingobject", "boolean", [_param("target", "TOUCHINGOBJECTMENU", "menu:touching")], "<touching [target]?>"),
    "touching_color": _spec("sensing_touchingcolor", "boolean", [_param("color", "COLOR", "color")], "<touching color [color]?>"),
    "color_is_touching": _spec("sensing_coloristouchingcolor", "boolean", [_param("color", "COLOR", "color"), _param("color2", "COLOR2", "color")], "<color [color] is touching [color2]?>"),
    "distance_to": _spec("sensing_distanceto", "reporter", [_param("target", "DISTANCETOMENU", "menu:distance")], "(distance to [target])"),
    "ask": _spec("sensing_askandwait", "stack", [_param("question", "QUESTION", "text")], "ask [question] and wait"),
    "answer": _spec("sensing_answer", "reporter", [], "(answer)"),
    "key_pressed": _spec("sensing_keypressed", "boolean", [_param("key", "KEY_OPTION", "menu:key")], "<key [key] pressed?>"),
    "mouse_down": _spec("sensing_mousedown", "boolean", [], "<mouse down?>"),
    "mouse_x": _spec("sensing_mousex", "reporter", [], "(mouse x)"),
    "mouse_y": _spec("sensing_mousey", "reporter", [], "(mouse y)"),
    "set_drag_mode": _spec("sensing_setdragmode", "stack", [_param("mode", "DRAG_MODE", "field:drag")], "set drag mode [mode]"),
    "loudness": _spec("sensing_loudness", "reporter", [], "(loudness)"),
    "timer": _spec("sensing_timer", "reporter", [], "(timer)"),
    "reset_timer": _spec("sensing_resettimer", "stack", [], "reset timer"),
    "property_of": _spec("sensing_of", "reporter", [_param("property", "PROPERTY", "field:property"), _param("target", "OBJECT", "menu:object")], "([property] of [target])"),
    "current": _spec("sensing_current", "reporter", [_param("unit", "CURRENTMENU", "field:current")], "(current [unit])"),
    "days_since_2000": _spec("sensing_dayssince2000", "reporter", [], "(days since 2000)"),
    "username": _spec("sensing_username", "reporter", [], "(username)"),
    # Operators
    "add": _spec("operator_add", "reporter", [_param("a", "NUM1", "number"), _param("b", "NUM2", "number")], "(a) + (b)"),
    "subtract": _spec("operator_subtract", "reporter", [_param("a", "NUM1", "number"), _param("b", "NUM2", "number")], "(a) - (b)"),
    "multiply": _spec("operator_multiply", "reporter", [_param("a", "NUM1", "number"), _param("b", "NUM2", "number")], "(a) * (b)"),
    "divide": _spec("operator_divide", "reporter", [_param("a", "NUM1", "number"), _param("b", "NUM2", "number")], "(a) / (b)"),
    "random": _spec("operator_random", "reporter", [_param("start", "FROM", "number"), _param("end", "TO", "number")], "pick random (start) to (end)"),
    "greater": _spec("operator_gt", "boolean", [_param("a", "OPERAND1", "text"), _param("b", "OPERAND2", "text")], "<a> > <b>"),
    "less": _spec("operator_lt", "boolean", [_param("a", "OPERAND1", "text"), _param("b", "OPERAND2", "text")], "<a> < <b>"),
    "equal": _spec("operator_equals", "boolean", [_param("a", "OPERAND1", "text"), _param("b", "OPERAND2", "text")], "<a> = <b>"),
    "both": _spec("operator_and", "boolean", [_param("a", "OPERAND1", "boolean"), _param("b", "OPERAND2", "boolean")], "<a> and <b>"),
    "either": _spec("operator_or", "boolean", [_param("a", "OPERAND1", "boolean"), _param("b", "OPERAND2", "boolean")], "<a> or <b>"),
    "not_": _spec("operator_not", "boolean", [_param("value", "OPERAND", "boolean")], "not <value>"),
    "join": _spec("operator_join", "reporter", [_param("a", "STRING1", "text"), _param("b", "STRING2", "text")], "join [a] [b]"),
    "letter": _spec("operator_letter_of", "reporter", [_param("index", "LETTER", "whole"), _param("text", "STRING", "text")], "letter (index) of [text]"),
    "mod": _spec("operator_mod", "reporter", [_param("a", "NUM1", "number"), _param("b", "NUM2", "number")], "(a) mod (b)"),
    "round": _spec("operator_round", "reporter", [_param("n", "NUM", "number")], "round (n)"),
    # Variables and lists
    "set": _spec("data_setvariableto", "stack", [_param("variable", "VARIABLE", "variable"), _param("value", "VALUE", "text")], "set [variable] to (value)"),
    "change": _spec("data_changevariableby", "stack", [_param("variable", "VARIABLE", "variable"), _param("value", "VALUE", "number")], "change [variable] by (value)"),
    "show_variable": _spec("data_showvariable", "stack", [_param("variable", "VARIABLE", "variable")], "show variable [variable]"),
    "hide_variable": _spec("data_hidevariable", "stack", [_param("variable", "VARIABLE", "variable")], "hide variable [variable]"),
    "add": _spec("data_addtolist", "stack", [_param("item", "ITEM", "text"), _param("list", "LIST", "list")], "add [item] to [list]"),
    "delete": _spec("data_deleteoflist", "stack", [_param("index", "INDEX", "index"), _param("list", "LIST", "list")], "delete (index) of [list]"),
    "delete_all": _spec("data_deletealloflist", "stack", [_param("list", "LIST", "list")], "delete all of [list]"),
    "insert": _spec("data_insertatlist", "stack", [_param("item", "ITEM", "text"), _param("index", "INDEX", "index"), _param("list", "LIST", "list")], "insert [item] at (index) of [list]"),
    "replace": _spec("data_replaceitemoflist", "stack", [_param("index", "INDEX", "index"), _param("list", "LIST", "list"), _param("item", "ITEM", "text")], "replace item (index) of [list] with [item]"),
    "item_of": _spec("data_itemoflist", "reporter", [_param("index", "INDEX", "index"), _param("list", "LIST", "list")], "item (index) of [list]"),
    "item_number": _spec("data_itemnumoflist", "reporter", [_param("item", "ITEM", "text"), _param("list", "LIST", "list")], "item # of [item] in [list]"),
    "show_list": _spec("data_showlist", "stack", [_param("list", "LIST", "list")], "show list [list]"),
    "hide_list": _spec("data_hidelist", "stack", [_param("list", "LIST", "list")], "hide list [list]"),
    "broadcast": _spec("event_broadcast", "stack", [_param("message", "BROADCAST_INPUT", "broadcast_input")], "broadcast [message]"),
    "broadcast_and_wait": _spec("event_broadcastandwait", "stack", [_param("message", "BROADCAST_INPUT", "broadcast_input")], "broadcast [message] and wait"),
    # Pen
    "erase_all": _spec("pen_clear", "stack", [], "erase all", "pen"),
    "stamp": _spec("pen_stamp", "stack", [], "stamp", "pen"),
    "pen_down": _spec("pen_penDown", "stack", [], "pen down", "pen"),
    "pen_up": _spec("pen_penUp", "stack", [], "pen up", "pen"),
    "set_pen_color": _spec("pen_setPenColorToColor", "stack", [_param("color", "COLOR", "color")], "set pen color to [color]", "pen"),
    "change_pen_color": _spec("pen_changePenHueBy", "stack", [_param("amount", "HUE", "number")], "change pen color by (amount)", "pen"),
    "set_pen_size": _spec("pen_setPenSizeTo", "stack", [_param("size", "SIZE", "number")], "set pen size to (size)", "pen"),
    "change_pen_size": _spec("pen_changePenSizeBy", "stack", [_param("amount", "SIZE", "number")], "change pen size by (amount)", "pen"),
    "set_pen": _spec("pen_setPenColorParamTo", "stack", [_param("param", "COLOR_PARAM", "field:pen"), _param("value", "VALUE", "number")], "set pen [param] to (value)", "pen"),
    "change_pen": _spec("pen_changePenColorParamBy", "stack", [_param("param", "COLOR_PARAM", "field:pen"), _param("value", "VALUE", "number")], "change pen [param] by (value)", "pen"),
}


MENUS = {
    "goto": ("motion_goto_menu", "TO"),
    "glide": ("motion_glideto_menu", "TO"),
    "point": ("motion_pointtowards_menu", "TOWARDS"),
    "touching": ("sensing_touchingobjectmenu", "TOUCHINGOBJECTMENU"),
    "distance": ("sensing_distancetomenu", "DISTANCETOMENU"),
    "key": ("sensing_keyoptions", "KEY_OPTION"),
    "costume": ("looks_costume", "COSTUME"),
    "backdrop": ("looks_backdrops", "BACKDROP"),
    "sound": ("sound_sounds_menu", "SOUND_MENU"),
    "clone": ("control_create_clone_of_menu", "CLONE_OPTION"),
    "object": ("sensing_of_object_menu", "OBJECT"),
}


DECLARATIONS = {"variable", "list", "dict", "costume", "sound", "backdrop", "sprite_name"}

MATH = {
    "abs": "abs",
    "floor": "floor",
    "ceiling": "ceiling",
    "sqrt": "sqrt",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
    "ln": "ln",
    "log": "log",
    "exp": "e ^",
    "power10": "10 ^",
}


# Editor popups, parameter names, and menu choices are declared in kitty.pyi.
def _export(name, doc, signature=None):
    def fn(*args, **kwargs):
        _compile_only(*args, **kwargs)

    fn.__name__ = name
    fn.__qualname__ = name
    fn.__doc__ = doc
    if signature is not None:
        fn.__signature__ = signature
    globals()[name] = fn


for _name, _spec_obj in BLOCKS.items():
    _export(_name, _spec_obj.doc, _spec_obj.python_signature())

for _name, _op in MATH.items():
    _export(_name, f"([{_op}] of (n))", Signature([Parameter("n", Parameter.POSITIONAL_OR_KEYWORD)]))

_export("math", "([op] of (n))", Signature([
    Parameter("op", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("n", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("length", "length of a list or of text", Signature([Parameter("value", Parameter.POSITIONAL_OR_KEYWORD)]))
_export("contains", "<container contains item?>", Signature([
    Parameter("container", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("item", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("green_flag", "when green flag clicked. Use as @kitty.green_flag.", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("when_key", 'when [key] key pressed. Use as @kitty.when_key("space").', Signature([
    Parameter("key", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("when_clicked", "when this sprite clicked", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("when_stage_clicked", "when stage clicked", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("when_backdrop", 'when backdrop switches to [name]', Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("when_loudness", "when loudness > (value)", Signature([
    Parameter("value", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("when_timer", "when timer > (value)", Signature([
    Parameter("value", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("when_receive", 'when I receive [message]', Signature([
    Parameter("message", Parameter.POSITIONAL_OR_KEYWORD),
]))
_export("when_cloned", "when I start as a clone", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("block", "Define a custom Scratch block.", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
    Parameter("warp", Parameter.KEYWORD_ONLY, default=False),
]))
_export("number", "Define a custom block that returns a number or text. Use return.", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
    Parameter("warp", Parameter.KEYWORD_ONLY, default=False),
]))
_export("boolean", "Define a custom block that returns a boolean. Use return.", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
    Parameter("warp", Parameter.KEYWORD_ONLY, default=False),
]))
_export("sprite", "Put the following function's scripts on a sprite.", Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("stage", "Put the following scripts on the stage.", Signature([
    Parameter("fn", Parameter.POSITIONAL_OR_KEYWORD, default=None),
]))
_export("variable", "Declare a Scratch variable.", Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, default=0),
    Parameter("shared", Parameter.KEYWORD_ONLY, default=False),
    Parameter("show", Parameter.KEYWORD_ONLY, default=False),
]))
_export("list", "Declare a Scratch list.", Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, default=None),
    Parameter("shared", Parameter.KEYWORD_ONLY, default=False),
    Parameter("show", Parameter.KEYWORD_ONLY, default=False),
]))
_export("dict", "Declare a dictionary stored as a keys list and a values list.", Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("value", Parameter.POSITIONAL_OR_KEYWORD, default=None),
    Parameter("shared", Parameter.KEYWORD_ONLY, default=False),
    Parameter("show", Parameter.KEYWORD_ONLY, default=False),
]))
_export("costume", "Add a costume file to this sprite.", Signature([
    Parameter("path", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("name", Parameter.KEYWORD_ONLY, default=None),
]))
_export("sound", "Add a sound file to this sprite.", Signature([
    Parameter("path", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("name", Parameter.KEYWORD_ONLY, default=None),
]))
_export("backdrop", "Add a backdrop file to the stage.", Signature([
    Parameter("path", Parameter.POSITIONAL_OR_KEYWORD),
    Parameter("name", Parameter.KEYWORD_ONLY, default=None),
]))
_export("sprite_name", "Set this sprite's name.", Signature([
    Parameter("name", Parameter.POSITIONAL_OR_KEYWORD),
]))

class Sprite:
    """A Scratch sprite.

    Subclass it, store state on self, and call Scratch blocks as methods.
    Each instance you create becomes its own sprite.
    """

    def __init__(self, *args, **kwargs):
        _compile_only()

    def clone(self):
        """create clone of [myself]"""
        _compile_only()


class Stage(Sprite):
    """The Scratch stage. Subclass it for backdrop scripts."""


def _bind_block_method(name, doc, signature):
    def method(self, *args, **kwargs):
        _compile_only()

    method.__name__ = name
    method.__qualname__ = f"Sprite.{name}"
    method.__doc__ = doc
    method.__signature__ = signature
    return method


for _name, _spec_obj in BLOCKS.items():
    if not hasattr(Sprite, _name):
        setattr(Sprite, _name, _bind_block_method(_name, _spec_obj.doc, _spec_obj.python_signature()))

for _name, _op in MATH.items():
    if not hasattr(Sprite, _name):
        setattr(Sprite, _name, _bind_block_method(
            _name,
            f"([{_op}] of (n))",
            Signature([Parameter("n", Parameter.POSITIONAL_OR_KEYWORD)]),
        ))

del _name, _spec_obj, _op, _bind_block_method
