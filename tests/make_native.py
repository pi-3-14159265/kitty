"""Write the project behind tests/native.sb3, in Scratch's own JSON.

    python tests/make_native.py native_source.sb3

It uses blocks the way the Scratch editor makes them, including ones Kitty's
compiler never writes: custom blocks with and without screen refresh, list
blocks that count from 1, an extension block, a cloud variable, comments,
off-center costumes, a hidden sprite, and a start backdrop.

tests/native.sb3 is this project after the Scratch VM (scratch-vm 5.0.300)
loaded it and saved it with vm.saveProjectSb3(), so it is in the exact form
Scratch writes. tests/run.py decompiles it and builds the result again.
"""
import hashlib
import json
import struct
import sys
import zipfile
import zlib


def png(width, height, rgb):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    rows = (b"\x00" + bytes(rgb) * width) * height
    head = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def wav():
    samples = bytes((128 + (40 if (i // 8) % 2 else -40)) for i in range(800))
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 8000, 1, 8)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(samples)) + samples
    return b"RIFF" + struct.pack("<I", len(body)) + body


def svg(width, height, fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<rect width="{width}" height="{height}" fill="{fill}"/></svg>').encode()


ASSETS = {}


def asset(name, data, ext, **extra):
    digest = hashlib.md5(data).hexdigest()
    ASSETS[f"{digest}.{ext}"] = data
    item = {"name": name, "assetId": digest, "md5ext": f"{digest}.{ext}", "dataFormat": ext}
    item.update(extra)
    return item


class Blocks:
    def __init__(self, prefix):
        self.prefix = prefix
        self.blocks = {}
        self.count = 0

    def new(self, opcode, inputs=None, fields=None, shadow=False, mutation=None):
        self.count += 1
        bid = f"{self.prefix}{self.count}"
        block = {"opcode": opcode, "next": None, "parent": None, "inputs": {}, "fields": fields or {},
                 "shadow": shadow, "topLevel": False}
        if mutation is not None:
            block["mutation"] = mutation
        self.blocks[bid] = block
        for name, value in (inputs or {}).items():
            block["inputs"][name] = self.inp(bid, value)
        return bid

    def inp(self, parent, value):
        kind = value[0]
        if kind == "num":
            return [1, [4, str(value[1])]]
        if kind == "text":
            return [1, [10, str(value[1])]]
        if kind == "color":
            return [1, [9, value[1]]]
        if kind == "bcast":
            return [1, [11, value[1], value[2]]]
        if kind == "var":
            return [3, [12, value[1], value[2]], [10, ""]]
        if kind == "list":
            return [3, [13, value[1], value[2]], [10, ""]]
        if kind == "menu":
            _k, opcode, field, choice = value
            shadow = self.new(opcode, fields={field: [choice, None]}, shadow=True)
            self.blocks[shadow]["parent"] = parent
            return [1, shadow]
        if kind == "rep":
            self.blocks[value[1]]["parent"] = parent
            return [3, value[1], [10, ""]]
        if kind == "bool":
            self.blocks[value[1]]["parent"] = parent
            return [2, value[1]]
        if kind == "stack":
            first = self.chain(value[1], parent)
            return [2, first]
        if kind == "proto":
            self.blocks[value[1]]["parent"] = parent
            return [1, value[1]]
        raise ValueError(kind)

    def chain(self, ids, parent):
        for index, bid in enumerate(ids):
            self.blocks[bid]["parent"] = parent if index == 0 else ids[index - 1]
            self.blocks[bid]["next"] = ids[index + 1] if index + 1 < len(ids) else None
        return ids[0] if ids else None

    def script(self, ids, x, y):
        self.chain(ids, None)
        top = self.blocks[ids[0]]
        top.update({"topLevel": True, "x": x, "y": y})
        return ids[0]

    # Shortcuts
    def join(self, a, b):
        return self.new("operator_join", {"STRING1": a, "STRING2": b})

    def add_to(self, item, name, lid):
        return self.new("data_addtolist", {"ITEM": item}, {"LIST": [name, lid]})


def procedure(b, proccode, args, warp):
    """args: list of (id, name, boolean). Returns (define_id, mutation_for_calls, {name: reporter factory})."""
    ids = [a[0] for a in args]
    names = [a[1] for a in args]
    mutation = {"tagName": "mutation", "children": [], "proccode": proccode,
                "argumentids": json.dumps(ids), "argumentnames": json.dumps(names),
                "argumentdefaults": json.dumps(["false" if a[2] else "" for a in args]), "warp": "true" if warp else "false"}
    proto = b.new("procedures_prototype", shadow=True, mutation=mutation)
    for arg_id, name, boolean in args:
        opcode = "argument_reporter_boolean" if boolean else "argument_reporter_string_number"
        reporter = b.new(opcode, fields={"VALUE": [name, None]}, shadow=True)
        b.blocks[reporter]["parent"] = proto
        b.blocks[proto]["inputs"][arg_id] = [1, reporter]
    define = b.new("procedures_definition", {"custom_block": ("proto", proto)})
    call_mutation = {"tagName": "mutation", "children": [], "proccode": proccode,
                     "argumentids": json.dumps(ids), "warp": "true" if warp else "false"}

    def arg(name, boolean=False):
        return b.new("argument_reporter_boolean" if boolean else "argument_reporter_string_number", fields={"VALUE": [name, None]})
    return define, call_mutation, arg


# ---------------------------------------------------------------- Stage
stage = Blocks("s")
done_hat = stage.new("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": ["done", "bDone"]})
stage.script([
    done_hat,
    stage.new("looks_switchbackdropto", {"BACKDROP": ("menu", "looks_backdrops", "BACKDROP", "night")}),
    stage.add_to(("rep", stage.join(("text", "stage "), ("rep", stage.new("looks_backdropnumbername", fields={"NUMBER_NAME": ["name", None]})))), "log", "lLog"),
], 0, 0)

# ---------------------------------------------------------------- Helper
helper = Blocks("h")
helper.script([
    helper.new("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": ["ping", "bPing"]}),
    helper.new("data_setvariableto", {"VALUE": ("rep", helper.join(("text", "ping "), ("var", "message", "vMsg")))}, {"VARIABLE": ["seen", "vSeen"]}),
    helper.new("data_changevariableby", {"VALUE": ("num", 0)}, {"VARIABLE": ["score", "vScore"]}),
], 0, 0)

# ---------------------------------------------------------------- Hero
b = Blocks("k")
walk_define, walk_call, walk_arg = procedure(b, "walk %s steps %b fast", [("aSteps", "steps", False), ("aFast", "fast", True)], warp=False)
walk_if = b.new("control_if_else", {
    "CONDITION": ("bool", walk_arg("fast", True)),
    "SUBSTACK": ("stack", [b.new("motion_movesteps", {"STEPS": ("num", 2)})]),
    "SUBSTACK2": ("stack", [b.new("motion_movesteps", {"STEPS": ("num", 1)})]),
})
walk_repeat = b.new("control_repeat", {
    "TIMES": ("rep", walk_arg("steps")),
    "SUBSTACK": ("stack", [walk_if, b.new("data_changevariableby", {"VALUE": ("num", 1)}, {"VARIABLE": ["t", "vT"]})]),
})
b.script([walk_define, walk_repeat], 600, 0)

fill_define, fill_call, fill_arg = procedure(b, "fill bag %s", [("aThing", "thing", False)], warp=True)
b.script([
    fill_define,
    b.add_to(("rep", fill_arg("thing")), "bag", "lBag"),
    b.new("data_insertatlist", {"ITEM": ("text", "first"), "INDEX": ("num", 1)}, {"LIST": ["bag", "lBag"]}),
    b.new("data_replaceitemoflist", {"INDEX": ("text", "last"), "ITEM": ("rep", b.join(("rep", fill_arg("thing")), ("text", "!")))}, {"LIST": ["bag", "lBag"]}),
    b.new("data_deleteoflist", {"INDEX": ("num", 2)}, {"LIST": ["bag", "lBag"]}),
    b.new("data_setvariableto", {"VALUE": ("rep", b.new("data_itemnumoflist", {"ITEM": ("text", "first")}, {"LIST": ["bag", "lBag"]}))}, {"VARIABLE": ["out", "vOut"]}),
], 600, 400)


def log(value):
    return b.add_to(value, "log", "lLog")


def rep(opcode, inputs=None, fields=None):
    return ("rep", b.new(opcode, inputs, fields))


elif_chain = b.new("control_if_else", {
    "CONDITION": ("bool", b.new("operator_gt", {"OPERAND1": ("var", "score", "vScore"), "OPERAND2": ("text", "5")})),
    "SUBSTACK": ("stack", [log(("text", "big"))]),
    "SUBSTACK2": ("stack", [b.new("control_if_else", {
        "CONDITION": ("bool", b.new("operator_equals", {"OPERAND1": ("var", "score", "vScore"), "OPERAND2": ("text", "0")})),
        "SUBSTACK": ("stack", [log(("text", "zero"))]),
        "SUBSTACK2": ("stack", [log(("text", "small"))]),
    })]),
})
countdown = b.new("control_repeat_until", {
    "CONDITION": ("bool", b.new("operator_lt", {"OPERAND1": ("var", "lives", "vLives"), "OPERAND2": ("text", "1")})),
    "SUBSTACK": ("stack", [
        b.new("data_changevariableby", {"VALUE": ("num", -1)}, {"VARIABLE": ["lives", "vLives"]}),
        log(("var", "lives", "vLives")),
    ]),
})
walk_call_block = b.new("procedures_call", {"aSteps": ("text", "5"), "aFast": ("bool", b.new("operator_not", {}))}, mutation=walk_call)
seen_of_helper = b.new("sensing_of", {"OBJECT": ("menu", "sensing_of_object_menu", "OBJECT", "Helper")}, {"PROPERTY": ["seen", None]})
x_of_stage = b.new("sensing_of", {"OBJECT": ("menu", "sensing_of_object_menu", "OBJECT", "_stage_")}, {"PROPERTY": ["backdrop name", None]})
drum = b.new("music_playDrumForBeats", {"DRUM": ("menu", "music_menu_DRUM", "DRUM", "1"), "BEATS": ("num", 0.25)})
green = [
    b.new("event_whenflagclicked"),
    b.new("motion_gotoxy", {"X": ("num", -100), "Y": ("num", 50)}),
    b.new("data_setvariableto", {"VALUE": ("text", "0")}, {"VARIABLE": ["t", "vT"]}),
    walk_call_block,
    b.new("data_setvariableto", {"VALUE": ("rep", b.join(("rep", b.join(("text", "t="), ("var", "t", "vT"))),
                                                         ("rep", b.join(("text", " x="), rep("motion_xposition")))))}, {"VARIABLE": ["out", "vOut"]}),
    log(("var", "out", "vOut")),
    b.new("procedures_call", {"aThing": ("text", "pear")}, mutation=fill_call),
    log(("rep", b.join(("text", "bag="), ("list", "bag", "lBag")))),
    log(("var", "out", "vOut")),
    log(rep("data_itemoflist", {"INDEX": ("num", 1)}, {"LIST": ["bag", "lBag"]})),
    log(rep("data_itemoflist", {"INDEX": ("rep", b.new("operator_add", {"NUM1": ("num", 1), "NUM2": ("num", 1)}))}, {"LIST": ["bag", "lBag"]})),
    log(rep("data_lengthoflist", {}, {"LIST": ["bag", "lBag"]})),
    log(("rep", b.new("data_listcontainsitem", {"ITEM": ("text", "PEAR!")}, {"LIST": ["bag", "lBag"]}))),
    log(rep("operator_round", {"NUM": ("rep", b.new("operator_divide", {"NUM1": ("num", 7), "NUM2": ("num", 2)}))})),
    log(rep("operator_mod", {"NUM1": ("num", -10), "NUM2": ("num", 3)})),
    log(rep("operator_mathop", {"NUM": ("num", 16)}, {"OPERATOR": ["sqrt", None]})),
    log(rep("operator_mathop", {"NUM": ("num", 30)}, {"OPERATOR": ["sin", None]})),
    log(rep("operator_letter_of", {"LETTER": ("num", 2), "STRING": ("text", "kitty")})),
    log(rep("operator_length", {"STRING": ("text", "kitty")})),
    log(("rep", b.new("operator_contains", {"STRING1": ("text", "kitty"), "STRING2": ("text", "TT")}))),
    log(("rep", b.join(("text", "007"), ("text", "1.50")))),
    log(rep("operator_subtract", {"NUM1": ("num", 3.14159265358979), "NUM2": ("num", 0.1)})),
    elif_chain,
    b.new("data_setvariableto", {"VALUE": ("num", 3)}, {"VARIABLE": ["lives", "vLives"]}),
    countdown,
    b.new("event_broadcastandwait", {"BROADCAST_INPUT": ("bcast", "ping", "bPing")}),
    log(("rep", b.join(("text", "helper saw "), ("rep", seen_of_helper)))),
    log(("rep", x_of_stage)),
    b.new("control_create_clone_of", {"CLONE_OPTION": ("menu", "control_create_clone_of_menu", "CLONE_OPTION", "_myself_")}),
    b.new("control_wait_until", {"CONDITION": ("bool", b.new("operator_gt", {"OPERAND1": ("var", "score", "vScore"), "OPERAND2": ("text", "0")}))}),
    log(("rep", b.join(("text", "score "), ("var", "score", "vScore")))),
    drum,
    b.new("looks_switchcostumeto", {"COSTUME": ("menu", "looks_costume", "COSTUME", "hero")}),
    b.new("looks_setsizeto", {"SIZE": ("num", 120)}),
    b.new("motion_pointindirection", {"DIRECTION": ("num", 90)}),
    b.new("event_broadcast", {"BROADCAST_INPUT": ("bcast", "done", "bDone")}),
]
b.script(green, 0, 0)
b.script([
    b.new("control_start_as_clone"),
    b.new("data_changevariableby", {"VALUE": ("num", 1)}, {"VARIABLE": ["score", "vScore"]}),
    b.new("control_delete_this_clone"),
], 0, 1400)
b.script([
    b.new("event_whenkeypressed", fields={"KEY_OPTION": ["space", None]}),
    b.new("looks_say", {"MESSAGE": ("text", "space")}),
], 0, 1600)
b.script([b.new("motion_movesteps", {"STEPS": ("num", 10)})], 0, 1800)  # never runs: no hat
b.blocks["floatvar"] = [12, "lives", "vLives", 400, 1900]

targets = [
    {
        "isStage": True, "name": "Stage",
        "variables": {"vScore": ["score", 0], "vCloud": ["☁ high", 7, True], "vMsg": ["message", "hi there"]},
        "lists": {"lLog": ["log", []]},
        "broadcasts": {"bPing": "ping", "bDone": "done"},
        "blocks": stage.blocks, "comments": {},
        "currentCostume": 1,
        "costumes": [
            asset("sky", svg(480, 360, "#88ccff"), "svg", bitmapResolution=1, rotationCenterX=240, rotationCenterY=180),
            asset("night", png(960, 720, (10, 10, 60)), "png", bitmapResolution=2, rotationCenterX=480, rotationCenterY=360),
        ],
        "sounds": [], "volume": 80, "layerOrder": 0, "tempo": 90,
        "videoTransparency": 50, "videoState": "on", "textToSpeechLanguage": None,
    },
    {
        "isStage": False, "name": "Helper",
        "variables": {"vSeen": ["seen", "nothing"]}, "lists": {}, "broadcasts": {},
        "blocks": helper.blocks, "comments": {},
        "currentCostume": 0,
        "costumes": [asset("helper", svg(40, 40, "#22aa55"), "svg", bitmapResolution=1, rotationCenterX=20, rotationCenterY=20)],
        "sounds": [], "volume": 100, "layerOrder": 1, "visible": False,
        "x": 100, "y": -50, "size": 100, "direction": 90, "draggable": False, "rotationStyle": "all around",
    },
    {
        "isStage": False, "name": "Hero",
        "variables": {"vLives": ["lives", 3], "vT": ["t", 0], "vOut": ["out", ""]},
        "lists": {"lBag": ["bag", ["a", 2]]}, "broadcasts": {},
        "blocks": b.blocks,
        "comments": {
            "c1": {"blockId": walk_call_block, "x": 0, "y": 0, "width": 200, "height": 100, "minimized": False,
                   "text": "Walk slowly so the steps show."},
            "c2": {"blockId": None, "x": 900, "y": 900, "width": 200, "height": 100, "minimized": False,
                   "text": "A note on the workspace."},
        },
        "currentCostume": 1,
        "costumes": [
            asset("hero", svg(64, 64, "#ff8800"), "svg", bitmapResolution=1, rotationCenterX=10, rotationCenterY=20),
            asset("small", png(40, 30, (200, 30, 30)), "png", bitmapResolution=2, rotationCenterX=5, rotationCenterY=5),
        ],
        "sounds": [asset("beep", wav(), "wav", rate=8000, sampleCount=800, format="")],
        "volume": 60, "layerOrder": 2, "visible": True,
        "x": -100, "y": 50, "size": 80, "direction": 45, "draggable": True, "rotationStyle": "left-right",
    },
]
monitors = [
    {"id": "vScore", "mode": "default", "opcode": "data_variable", "params": {"VARIABLE": "score"}, "spriteName": None,
     "value": 0, "width": 0, "height": 0, "x": 5, "y": 5, "visible": True, "sliderMin": 0, "sliderMax": 100, "isDiscrete": True},
    {"id": "lBag", "mode": "list", "opcode": "data_listcontents", "params": {"LIST": "bag"}, "spriteName": "Hero",
     "value": [], "width": 0, "height": 0, "x": 5, "y": 40, "visible": True},
]
project = {"targets": targets, "monitors": monitors, "extensions": ["music"],
           "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "fixture"}}
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("project.json", json.dumps(project))
    for name, data in ASSETS.items():
        archive.writestr(name, data)
print(sys.argv[1])
