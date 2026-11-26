"""Test Kitty: compile the suite, check what must compile and what must not,
then run the suite on Scratch.

    python tests/run.py
    python tests/run.py --no-scratch

The last step builds tests/project into tests/suite.sb3, decompiles that with
kitty decomp, builds the decompiled Python again, and runs both projects in
Scratch's engine (kitty run's player) in a browser. Each must finish with
failed 0. A headless Microsoft Edge, Google Chrome, or Chromium runs it with
no window; without one, your default browser opens the page. --no-scratch
skips this step.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import webbrowser
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from comp import CompileError, comp
import cli

SUITE = ROOT / "tests" / "suite.sb3"
PROJECT = ROOT / "tests" / "project"
PARSER = Path(r"C:\Users\thaya\AppData\Local\Temp\scratchparse\check.js")
TMP = ROOT / "tests" / "_reject"

# Each snippet must fail to compile, and the message must contain the text.
REJECTS = [
    (
        "ignored call",
        "ignored function",
        "import numpy\n\n@ignore\ndef numpyFunc():\n    numpy.mean([1, 2])\n\nnumpyFunc()\n",
    ),
    (
        "ignored call in hat",
        "ignored function",
        "import numpy\n\n@ignore\ndef numpyFunc():\n    numpy.mean([1, 2])\n\n@kitty.green_flag\ndef start():\n    numpyFunc()\n",
    ),
    (
        "ragged",
        "rectangular",
        "grid = [[1, 2], [3]]\n",
    ),
    (
        "ragged runtime",
        "rectangular",
        "def build():\n    grid = [[1, 2], [3]]\n",
    ),
    (
        "range step",
        "range step cannot be 0",
        "for i in range(3, 0, 0):\n    pass\n",
    ),
    (
        "empty range",
        "unknown name",
        "import kitty\nfor i in range(0):\n    pass\nkitty.say(i)\n",
    ),
    (
        "tuple item",
        "tuple cannot be changed",
        "point = (1, 2)\npoint[0] = 9\n",
    ),
    (
        "block return",
        "return belongs",
        "import kitty\n\n@kitty.block\ndef show():\n    return 1\n",
    ),
    (
        "star args",
        "pass at most",
        "def total(first, *args):\n    return first\n\ntotal(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)\n",
    ),
    (
        "kwargs",
        "pass at most",
        "def show(**kwargs):\n    return kwargs['a']\n\nshow(a=1, b=2, c=3, d=4, e=5)\n",
    ),
    (
        "format spec",
        "f-string format specs",
        "import kitty\nn = 1\nkitty.say(f'{n:.2f}')\n",
    ),
    (
        "slice assign",
        "slice assignment",
        "items = [1, 2, 3]\nitems[0:2] = [9]\n",
    ),
    (
        "break",
        "break is outside",
        "break\n",
    ),
    (
        "continue",
        "continue is outside",
        "continue\n",
    ),
    (
        "rank",
        "dimensions",
        "grid = [[1, 2], [3, 4]]\ngrid = [[[1], [2]], [[3], [4]]]\n",
    ),
    (
        "grid param",
        "dimensions",
        "def paint(grid):\n    grid[0][1] = 8\n\nitems = [1, 2, 3, 4]\npaint(items)\n",
    ),
    (
        "positional",
        "without /",
        "def add(a, /, b):\n    return a + b\n",
    ),
    (
        "mixed return",
        "same kind",
        "def bad(n):\n    if n == 0:\n        items = []\n        return items\n    return 1\n",
    ),
    (
        "return width",
        "same number",
        "def bad(n):\n    if n:\n        return 1, 2\n    return 1\n",
    ),
    (
        "div zero",
        "division by zero",
        "n = 1 / 0\n",
    ),
    (
        "set item",
        "set has no positions",
        "seen = {1, 2}\nseen[0] = 3\n",
    ),
    (
        "text item",
        "text cannot be changed",
        "word = 'hi'\nword[0] = 'H'\n",
    ),
    (
        "unknown block",
        "unknown Scratch block",
        "import kitty\nkitty.not_a_block()\n",
    ),
]


def green_flags(sb3):
    with zipfile.ZipFile(sb3) as archive:
        project = json.loads(archive.read("project.json"))
    counts = {}
    vm = project.get("meta", {}).get("vm")
    for target in project["targets"]:
        count = 0
        blocks = target.get("blocks", {})
        for block in blocks.values():
            if (
                isinstance(block, dict)
                and block.get("opcode") == "event_whenflagclicked"
                and block.get("parent") is None
            ):
                count += 1
        counts[target["name"]] = count
    return vm, counts


def compile_cli_aliases():
    failures = []
    if os.name == "nt":
        cli._ensure_windows_launchers()
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            launcher_dir = Path(local_app_data) / "Microsoft" / "WindowsApps"
            for name in ("kitty.cmd", "kitty-build.cmd", "kitty-decomp.cmd"):
                if not (launcher_dir / name).is_file():
                    failures.append(f"{name}: Windows launcher was not created")
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    script = TMP / "game.py"
    script.write_text(
        "import kitty\n@kitty.green_flag\ndef start():\n    kitty.say(\"alias\")\n",
        encoding="utf-8",
    )
    for alias in ("build", "compile", "comp"):
        output = TMP / f"{alias}.sb3"
        code = cli.main([alias, str(script), "-o", str(output)])
        if code != 0:
            failures.append(f"{alias}: CLI returned {code}")
        elif not output.is_file():
            failures.append(f"{alias}: output was not created")
    shutil.rmtree(TMP, ignore_errors=True)
    return failures


def compile_ignored():
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    folder = TMP / "ignored"
    folder.mkdir()
    cases = [
        "import numpy\n\n@ignore\ndef numpyFunc():\n    return numpy.mean([1, 2])\n",
        "import numpy\n\n@ignore()\ndef numpyFunc():\n    return numpy.mean([1, 2])\n",
        "import kitty\nimport numpy\n\n@kitty.ignore\ndef numpyFunc():\n    return numpy.mean([1, 2])\n",
    ]
    for number, source in enumerate(cases):
        script = folder / f"case{number}.py"
        script.write_text(source, encoding="utf-8")
        output = folder / f"case{number}.sb3"
        warnings = []
        try:
            comp(script, output, warnings)
            if not any("numpy imported and cannot be compiled" in warning for warning in warnings):
                failures.append(f"ignored case {number}: missing numpy import warning")
        except CompileError as exc:
            failures.append(f"ignored case {number}: {exc}")
    shutil.rmtree(TMP, ignore_errors=True)
    return failures


# Each loop test runs blocks before it can be read. Those blocks must run
# again inside the loop, or the loop keeps reading its first answer.
LOOP_TESTS = [
    (
        "while in",
        'import kitty\nitems = ["a"]\n\n@kitty.green_flag\ndef start():\n'
        '    while "z" not in items:\n        items.append("z")\n',
    ),
    (
        "while call",
        "import kitty\nn = 0\n\ndef big(v):\n    return v > 10\n\n@kitty.green_flag\ndef start():\n"
        "    global n\n    while not big(n):\n        n += 1\n",
    ),
    (
        "repeat_until in",
        'import kitty\nitems = ["a"]\n\n@kitty.green_flag\ndef start():\n'
        '    with kitty.repeat_until("z" in items):\n        items.append("z")\n',
    ),
    (
        "wait_until in",
        'import kitty\nitems = ["a"]\n\n@kitty.green_flag\ndef start():\n'
        '    kitty.wait_until("z" in items)\n',
    ),
]


def _subtree(blocks, block_id, follow_next):
    found = []
    stack = [block_id]
    while stack:
        current = stack.pop()
        if not isinstance(current, str) or current not in blocks:
            continue
        found.append(blocks[current])
        if follow_next:
            stack.append(blocks[current].get("next"))
        for value in blocks[current].get("inputs", {}).values():
            if isinstance(value, list) and len(value) > 1:
                stack.append(value[1])
    return found


def _loop_rereads_test(sb3):
    with zipfile.ZipFile(sb3) as archive:
        project = json.loads(archive.read("project.json"))
    for target in project["targets"]:
        blocks = target.get("blocks", {})
        for block in blocks.values():
            if not isinstance(block, dict) or block.get("opcode") != "control_repeat_until":
                continue
            condition = block.get("inputs", {}).get("CONDITION", [None, None])[1]
            body = block.get("inputs", {}).get("SUBSTACK", [None, None])[1]
            read = {
                item["fields"]["VARIABLE"][0]
                for item in _subtree(blocks, condition, False)
                if item.get("opcode") == "data_variable"
            }
            written = {
                item["fields"]["VARIABLE"][0]
                for item in _subtree(blocks, body, True)
                if item.get("opcode") == "data_setvariableto"
            }
            if read & written:
                return True
    return False


def compile_loop_tests():
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        for name, source in LOOP_TESTS:
            folder = TMP / name.replace(" ", "_")
            folder.mkdir()
            script = folder / "case.py"
            script.write_text(source, encoding="utf-8")
            output = folder / "case.sb3"
            try:
                comp(script, output)
            except CompileError as exc:
                failures.append(f"{name}: {exc}")
                continue
            if not _loop_rereads_test(output):
                failures.append(f"{name}: the loop test is worked out once, before the loop")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


def _png(width, height):
    """A plain white PNG of this size."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    rows = (b"\x00" + b"\xff\xff\xff" * width) * height
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def _jpg_header(width, height, orientation=1):
    """The start of a JPEG, with an EXIF orientation: enough for the compiler to read its size."""
    tiff = b"II*\x00" + struct.pack("<IH", 8, 1) + struct.pack("<HHIHH", 0x0112, 3, 1, orientation, 0) + struct.pack("<I", 0)
    exif = b"Exif\x00\x00" + tiff
    frame = struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00"
    return (
        b"\xff\xd8\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif
        + b"\xff\xc0" + struct.pack(">H", len(frame) + 2) + frame + b"\xff\xd9"
    )


IMAGE_FILES = {
    "wide.png": lambda: _png(100, 60),
    "odd.png": lambda: _png(5, 3),
    "huge.png": lambda: _png(500, 10),
    "photo.jpg": lambda: _jpg_header(120, 80),
    "turned.jpg": lambda: _jpg_header(120, 80, orientation=6),
    "really-png.jpg": lambda: _png(10, 10),
    "box.svg": lambda: b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="-10 0 64 32"/>',
    "sized.svg": lambda: b'<svg xmlns="http://www.w3.org/2000/svg" width="40px" height="20"/>',
    "bare.svg": lambda: b'<svg xmlns="http://www.w3.org/2000/svg"/>',
    "cat.gif": lambda: b"GIF89a" + bytes(20),
    "ping.wav": lambda: b"RIFF\x04\x00\x00\x00WAVE",
}

# (script name, declaration, expected costume fields; None means the field is left out)
IMAGE_COSTUMES = [
    ("case", 'kitty.costume("wide.png")', {"dataFormat": "png", "bitmapResolution": 1, "rotationCenterX": 50, "rotationCenterY": 30}),
    ("case", 'kitty.costume("wide.png", resolution=2)', {"bitmapResolution": 2, "rotationCenterX": 50, "rotationCenterY": 30}),
    ("case", 'kitty.costume("odd.png")', {"rotationCenterX": 2.5, "rotationCenterY": 1.5}),
    ("case", 'kitty.costume("photo.jpg")', {"dataFormat": "jpg", "rotationCenterX": 60, "rotationCenterY": 40}),
    ("case", 'kitty.costume("turned.jpg")', {"rotationCenterX": 40, "rotationCenterY": 60}),
    ("case", 'kitty.costume("really-png.jpg")', {"dataFormat": "png", "rotationCenterX": 5}),
    ("case", 'kitty.costume("box.svg")', {"dataFormat": "svg", "bitmapResolution": 1, "rotationCenterX": 22, "rotationCenterY": 16}),
    ("case", 'kitty.costume("sized.svg")', {"rotationCenterX": 20, "rotationCenterY": 10}),
    ("case", 'kitty.costume("bare.svg")', {"rotationCenterX": None, "rotationCenterY": None}),
    ("case", 'kitty.costume("wide.png", center=(1, 2.5))', {"rotationCenterX": 1, "rotationCenterY": 2.5}),
    ("case", 'kitty.costume("bare.svg", center=(7, 8))', {"rotationCenterX": 7, "rotationCenterY": 8}),
    ("stage", 'kitty.backdrop("wide.png", name="field")', {"name": "field", "rotationCenterX": 50, "rotationCenterY": 30}),
]

# (declaration, text that must be in the error)
IMAGE_REJECTS = [
    ('kitty.costume("cat.gif")', "svg, png, or jpg"),
    ('kitty.costume("wide.png", resolution=3)', "resolution is 1 or 2"),
    ('kitty.costume("box.svg", resolution=2)', "resolution is for png and jpg"),
    ('kitty.sound("ping.wav", resolution=2)', "resolution and center belong on a costume"),
    ('kitty.costume("wide.png", center=5)', "center is two numbers"),
]

# (declaration, text that must be in a warning, or None for no warning)
IMAGE_WARNINGS = [
    ('kitty.costume("huge.png")', "500 x 10, bigger than the 480 x 360 stage"),
    ('kitty.costume("huge.png", resolution=2)', None),
    ('kitty.costume("bare.svg")', "no viewBox"),
    ('kitty.costume("bare.svg", center=(7, 8))', None),
    ('kitty.costume("box.svg")', None),
]


def _image_case(folder, script_name, line):
    folder.mkdir()
    for name, make in IMAGE_FILES.items():
        (folder / name).write_bytes(make())
    script = folder / f"{script_name}.py"
    script.write_text(f"import kitty\n{line}\n", encoding="utf-8")
    output = folder / "case.sb3"
    warnings = []
    comp(script, output, warnings)
    with zipfile.ZipFile(output) as archive:
        project = json.loads(archive.read("project.json"))
    target = next(item for item in project["targets"] if item["isStage"] == (script_name == "stage"))
    return target["costumes"][0], warnings


def compile_images():
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    count = 0

    def folder():
        nonlocal count
        count += 1
        return TMP / f"image{count}"

    try:
        for script_name, line, expected in IMAGE_COSTUMES:
            try:
                costume, _warnings = _image_case(folder(), script_name, line)
            except CompileError as exc:
                failures.append(f"{line}: {exc}")
                continue
            for key, want in expected.items():
                if costume.get(key) != want:
                    failures.append(f"{line}: {key} is {costume.get(key)!r}, expected {want!r}")
        for line, needle in IMAGE_REJECTS:
            try:
                _image_case(folder(), "case", line)
            except CompileError as exc:
                if needle not in str(exc):
                    failures.append(f"{line}: expected {needle!r} in {exc}")
            else:
                failures.append(f"{line}: compiled, but it must be rejected")
        for line, needle in IMAGE_WARNINGS:
            try:
                _costume, warnings = _image_case(folder(), "case", line)
            except CompileError as exc:
                failures.append(f"{line}: {exc}")
                continue
            if needle is None and warnings:
                failures.append(f"{line}: unexpected warning {warnings}")
            elif needle is not None and not any(needle in warning for warning in warnings):
                failures.append(f"{line}: expected a warning with {needle!r}, got {warnings}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


NATIVE = ROOT / "tests" / "native.sb3"


def _project_json(sb3):
    with zipfile.ZipFile(sb3) as archive:
        return json.loads(archive.read("project.json"))


def _proccodes_unique(project):
    """Scratch finds a custom block by its proccode, so two definitions must not share one."""
    problems = []
    for target in project["targets"]:
        codes = [
            block["mutation"]["proccode"]
            for block in target["blocks"].values()
            if isinstance(block, dict) and block.get("opcode") == "procedures_prototype"
        ]
        for code in sorted({code for code in codes if codes.count(code) > 1}):
            problems.append(f"{target['name']}: two custom blocks are both {code!r}")
    return problems


def _names(target):
    """Variable and list names the script chose. Kitty's own start with a dot."""
    found = {("var", item[0]) for item in target["variables"].values()}
    found |= {("list", item[0]) for item in target["lists"].values()}
    return {item for item in found if not item[1].startswith(".")}


def compile_decomp():
    """kitty decomp writes a Kitty project that kitty build turns back into the same project."""
    import decomp

    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        original = _project_json(SUITE)
        failures.extend(_proccodes_unique(original))
        folder = TMP / "suite"
        if cli.main(["decomp", str(SUITE), str(folder)]) != 0:
            return failures + ["kitty decomp tests/suite.sb3 failed"]
        for name in ("Assets", "Sounds", "stage.py", "suite.py", "felix.py", "blocksAsText.txt"):
            if not (folder / name).exists():
                failures.append(f"decomp suite: {name} is missing")
        try:
            decomp.decomp(SUITE, folder)
        except FileExistsError:
            pass
        else:
            failures.append("decomp suite: wrote into a folder that already had files")
        rebuilt = _project_json(comp(folder, TMP / "suite.sb3"))
        failures.extend(_proccodes_unique(rebuilt))
        before = {target["name"]: target for target in original["targets"]}
        after = {target["name"]: target for target in rebuilt["targets"]}
        if set(before) != set(after):
            failures.append(f"decomp suite: sprites {sorted(before)} became {sorted(after)}")
        for name in set(before) & set(after):
            if [c["name"] for c in before[name]["costumes"]] != [c["name"] for c in after[name]["costumes"]]:
                failures.append(f"decomp suite: {name} costumes changed")
            missing = _names(before[name]) - _names(after[name])
            if missing:
                failures.append(f"decomp suite: {name} lost {sorted(missing)}")

        warnings = []
        folder = TMP / "native"
        decomp.decomp(NATIVE, folder, warnings)
        expected = ["cloud variable '☁ high'", "music_playDrumForBeats has no Kitty block"]
        if len(warnings) != len(expected) or not all(any(e in w for w in warnings) for e in expected):
            failures.append(f"decomp native: warnings were {warnings}")
        hero_source = (folder / "Hero.py").read_text(encoding="utf-8")
        for line in ("@kitty.block(warp=False)", 'bag.insert(0, "first")', "elif score == 0:", "log.append(bag[1])",
                     'kitty.join("007", "1.50")', "kitty.costume(\"Assets/hero.svg\", center=(10, 20))"):
            if line not in hero_source:
                failures.append(f"decomp native: Hero.py has no {line!r}")
        rebuilt = _project_json(comp(folder, TMP / "native.sb3"))
        failures.extend(_proccodes_unique(rebuilt))
        targets = {target["name"]: target for target in rebuilt["targets"]}
        checks = [
            ("Hero", "x", -100), ("Hero", "y", 50), ("Hero", "size", 80), ("Hero", "direction", 45),
            ("Hero", "rotationStyle", "left-right"), ("Hero", "draggable", True), ("Hero", "volume", 60),
            ("Hero", "currentCostume", 1), ("Hero", "layerOrder", 2), ("Helper", "visible", False),
            ("Helper", "layerOrder", 1), ("Stage", "currentCostume", 1), ("Stage", "tempo", 90), ("Stage", "volume", 80),
        ]
        for name, key, want in checks:
            if targets.get(name, {}).get(key) != want:
                failures.append(f"decomp native: {name} {key} is {targets.get(name, {}).get(key)!r}, expected {want!r}")
        costumes = [(c["name"], c["bitmapResolution"], c.get("rotationCenterX"), c.get("rotationCenterY"))
                    for c in targets["Hero"]["costumes"]]
        if costumes != [("hero", 1, 10, 20), ("small", 2, 5, 5)]:
            failures.append(f"decomp native: Hero costumes are {costumes}")
        walk = [block["mutation"]["warp"] for block in targets["Hero"]["blocks"].values()
                if isinstance(block, dict) and block.get("opcode") == "procedures_prototype"
                and block["mutation"]["proccode"].startswith("walk steps fast")]
        if not walk or any(str(warp).lower() != "false" for warp in walk):
            failures.append(f"decomp native: walk runs without screen refresh ({walk})")
        shown = sorted(monitor["params"].get("VARIABLE") or monitor["params"].get("LIST") for monitor in rebuilt["monitors"])
        if shown != ["bag", "score"]:
            failures.append(f"decomp native: monitors are {shown}")
    except (CompileError, OSError, KeyError, ValueError) as exc:
        failures.append(f"decomp: {type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


# Each case is a dict of file name to source. A string expect is text that must be in the error.
LANGUAGE_CASES = [
    (
        "shared across files",
        {"stage.py": "import kitty\nscore = 5\n",
         "cat.py": "import kitty\nscore = kitty.variable('score', 5, shared=True)\n\n@kitty.green_flag\ndef go():\n    global score\n    score += 1\n"},
        None,
    ),
    (
        "shared mismatch",
        {"stage.py": "import kitty\nscore = 5\n", "cat.py": "import kitty\nscore = kitty.variable('score', 6, shared=True)\n"},
        "starts at",
    ),
    (
        "inner block name",
        {"cat.py": "import kitty\n\ndef greet(name):\n    kitty.say(name)\n\ndef greet_run(name, other):\n    kitty.say(other)\n\n"
                   "@kitty.green_flag\ndef go():\n    greet('a')\n    greet_run('b', 'c')\n"},
        None,
    ),
    (
        "start_with",
        {"cat.py": "import kitty\nkitty.start_with(x=-10, y=20, visible=False, size=50, layer=1)\n"},
        None,
    ),
    ("start_with key", {"cat.py": "import kitty\nkitty.start_with(speed=3)\n"}, "start_with on a sprite takes"),
    ("start_with stage", {"stage.py": "import kitty\nkitty.start_with(x=3)\n"}, "start_with on the stage takes"),
    ("start_with costume", {"cat.py": "import kitty\nkitty.start_with(costume='nope')\n"}, "is not a costume"),
]


def compile_language():
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        for number, (name, files, expect) in enumerate(LANGUAGE_CASES):
            folder = TMP / f"case{number}"
            folder.mkdir()
            for file_name, source in files.items():
                (folder / file_name).write_text(source, encoding="utf-8")
            try:
                project = _project_json(comp(folder, folder / "out.sb3"))
            except CompileError as exc:
                if expect is None or expect not in str(exc):
                    failures.append(f"{name}: {exc}")
                continue
            if expect is not None:
                failures.append(f"{name}: compiled, but it must be rejected")
                continue
            failures.extend(f"{name}: {problem}" for problem in _proccodes_unique(project))
            targets = {target["name"]: target for target in project["targets"]}
            if name == "shared across files":
                stage_vars = [item[0] for item in targets["Stage"]["variables"].values()]
                if stage_vars.count("score") != 1 or targets["cat"]["variables"]:
                    failures.append(f"{name}: variables are {stage_vars} and {targets['cat']['variables']}")
            if name == "start_with":
                cat = targets["cat"]
                got = (cat["x"], cat["y"], cat["visible"], cat["size"])
                if got != (-10, 20, False, 50):
                    failures.append(f"{name}: cat starts as {got}")

        # warp=False keeps screen refresh; a plain def runs without it, as before.
        folder = TMP / "warp"
        folder.mkdir()
        (folder / "cat.py").write_text(
            "import kitty\n\n@kitty.block(warp=False)\ndef walk():\n    kitty.move(1)\n\n"
            "def dash():\n    kitty.move(1)\n\n@kitty.green_flag\ndef go():\n    walk()\n    dash()\n"
            "    kitty.say(3.14159265358979)\n",
            encoding="utf-8",
        )
        project = _project_json(comp(folder / "cat.py", folder / "out.sb3"))
        blocks = project["targets"][1]["blocks"].values()
        for prefix, want in (("walk", "false"), ("dash", "true")):
            warps = {str(block["mutation"]["warp"]).lower() for block in blocks
                     if isinstance(block, dict) and block.get("opcode") in ("procedures_prototype", "procedures_call")
                     and block["mutation"]["proccode"].startswith(prefix)}
            if warps != {want}:
                failures.append(f"warp: {prefix} blocks have warp {warps}, expected {want}")
        said = [block["inputs"]["MESSAGE"][1][1] for block in blocks
                if isinstance(block, dict) and block.get("opcode") == "looks_say"]
        if said != ["3.14159265358979"]:
            failures.append(f"number text: say got {said}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


def compile_player():
    """kitty run serves the player, the project, and the bundled Scratch runtime, and nothing else."""
    import hashlib
    import urllib.error
    import urllib.request

    import kitty_player

    failures = []
    for line in (kitty_player.VENDOR / "SOURCES.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("https://"):
            path = kitty_player.VENDOR / parts[0]
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != parts[1]:
                failures.append(f"player: vendor/{parts[0]} does not match SOURCES.txt")

    project = kitty_player.Project(SUITE, verbose=True)
    if not project.load():
        return failures + [f"player: suite.sb3 did not load: {project.error}"]
    server = kitty_player.serve(project)
    base = f"http://127.0.0.1:{server.server_port}"

    def get(path, data=None):
        request = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, b""

    try:
        # --verbose: the page reports with the token from /status; anything else is refused.
        lines = json.dumps(["player check"]).encode("utf-8")
        status, _body = get(f"/log?token={project.token}", lines)
        if status != 204:
            failures.append(f"player: /log with the token returned {status}")
        for path in ("/log?token=wrong", "/log"):
            status, _body = get(path, lines)
            if status != 403:
                failures.append(f"player: {path} returned {status}, expected 403")
        status, body = get("/chunks/fetch-worker.cd3a909d7b876aabf94a.js")
        if status != 200 or not body:
            failures.append(f"player: scratch-storage's worker returned {status}")
        status, page = get("/")
        if status != 200 or b"vendor/scratch-vm.js" not in page:
            failures.append(f"player: / returned {status}")
        status, body = get("/status")
        info = json.loads(body) if status == 200 else {}
        if info.get("title") != "suite.sb3" or not info.get("ready") or info.get("error"):
            failures.append(f"player: /status returned {status} {info}")
        status, body = get("/project.sb3")
        if status != 200 or body != SUITE.read_bytes():
            failures.append(f"player: /project.sb3 returned {status}")
        for name in ("scratch-vm.js", "scratch-audio.js", "licenses/scratch-vm.LICENSE"):
            status, body = get(f"/vendor/{name}")
            if status != 200 or body != (kitty_player.VENDOR / name).read_bytes():
                failures.append(f"player: /vendor/{name} returned {status}")
        for path in ("/vendor/../__init__.py", "/vendor/%2e%2e/__init__.py", "/../LICENSE", "/nothing"):
            status, _body = get(path)
            if status != 404:
                failures.append(f"player: {path} returned {status}, expected 404")
    finally:
        server.shutdown()
        server.server_close()

    # kitty run plays .sb3 files only, and checks that a file is one before it serves it.
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        (TMP / "cat.py").write_text("import kitty\n", encoding="utf-8")
        (TMP / "fake.sb3").write_text("not a zip", encoding="utf-8")
        for source in (TMP / "cat.py", TMP, TMP / "fake.sb3", TMP / "missing.sb3"):
            if kitty_player.main([str(source), "--no-browser"]) != 1:
                failures.append(f"player: kitty run {source.name} did not refuse it")
        fake = kitty_player.Project(TMP / "fake.sb3")
        if fake.load() or "is not a Scratch .sb3 file" not in (fake.error or ""):
            failures.append(f"player: a file that is not an .sb3 reported {fake.error!r}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


def compile_rejects():
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        for name, needle, source in REJECTS:
            folder = TMP / name.replace(" ", "_")
            folder.mkdir()
            script = folder / "case.py"
            script.write_text(source, encoding="utf-8")
            output = folder / "case.sb3"
            try:
                comp(script, output)
            except CompileError as exc:
                text = str(exc)
                if needle not in text:
                    failures.append(f"{name}: expected {needle!r} in {text}")
            else:
                failures.append(f"{name}: compiled, but it must be rejected")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


def _find_browser():
    """A Chromium browser that can run headless: Microsoft Edge, Google Chrome, or Chromium."""
    candidates = []
    if os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidates.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    elif sys.platform == "darwin":
        for app in ("Google Chrome", "Microsoft Edge", "Chromium"):
            candidates.append(Path(f"/Applications/{app}.app/Contents/MacOS/{app}"))
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    return next((path for path in candidates if path.is_file()), None)


def run_on_scratch(sb3, timeout=180):
    """Play sb3 in Scratch's engine in a browser, run the green flag, and return (result, how).

    result is what the page reports: seconds, timedOut, errors, and every sprite's
    variables and lists. It is None when no browser reported back.
    """
    import kitty_player

    project = kitty_player.Project(sb3)
    if not project.load():
        return None, project.error
    server = kitty_player.serve(project)
    url = f"http://127.0.0.1:{server.server_port}/?test={project.token}"
    browser = _find_browser()
    profile = tempfile.mkdtemp(prefix="kitty-scratch-test-")
    process = None
    try:
        if browser is not None:
            how = f"headless {browser.stem}"
            # A fresh profile keeps this browser apart from any you have open. The fake
            # microphone lets the loudness block work without asking.
            process = subprocess.Popen(
                [
                    str(browser), "--headless=new", f"--user-data-dir={profile}", "--no-first-run",
                    "--no-default-browser-check", "--autoplay-policy=no-user-gesture-required",
                    "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            how = "your browser"
            if not webbrowser.open(url):
                return None, "no browser could be opened"
        if not project.finished.wait(timeout):
            return None, f"{how} sent no result within {timeout} seconds"
        return project.result, how
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
        server.shutdown()
        server.server_close()
        shutil.rmtree(profile, ignore_errors=True)


def run_suites_on_scratch():
    """Build, decompile, build again, and run both suites on Scratch. Each must end with failed 0."""
    import decomp

    if "--no-scratch" in sys.argv:
        print("running on Scratch: skipped (--no-scratch)")
        return []
    failures = []
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    try:
        folder = TMP / "roundtrip"
        decomp.decomp(SUITE, folder)
        rebuilt = comp(folder, TMP / "roundtrip.sb3")
        for label, sb3 in (("built suite", SUITE), ("build, decomp, recomp", rebuilt)):
            result, how = run_on_scratch(sb3)
            if result is None:
                failures.append(f"on Scratch, {label}: {how}")
                continue
            suite = result.get("targets", {}).get("suite", {})
            passed = suite.get("vars", {}).get("passed")
            failed = suite.get("vars", {}).get("failed")
            names = suite.get("lists", {}).get("failed tests", [])
            print(f"on Scratch ({how}), {label}: passed {passed}, failed {failed}, {result.get('seconds', 0):.1f} s")
            if result.get("timedOut"):
                failures.append(f"on Scratch, {label}: still running after the time limit")
            if failed != "0" or passed in (None, "0"):
                failures.append(f"on Scratch, {label}: passed {passed}, failed {failed}: {', '.join(names)}")
            for error in result.get("errors") or []:
                failures.append(f"on Scratch, {label}: page error: {error}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return failures


def main():
    print("compiling", PROJECT, "->", SUITE)
    comp(PROJECT, SUITE)
    vm, flags = green_flags(SUITE)
    print("meta.vm", vm)
    print("green flags", flags)
    problems = []
    if vm != "3.0.0-kitty":
        problems.append(f"meta.vm is {vm!r}")
    if flags.get("suite") != 1:
        problems.append(f"suite sprite has {flags.get('suite')} green-flag scripts, expected 1")
    if PARSER.is_file():
        result = subprocess.run(
            ["node", str(PARSER), str(SUITE)],
            capture_output=True,
            text=True,
        )
        print(result.stdout.strip() or result.stderr.strip())
        if result.returncode != 0:
            problems.append("scratch-parser rejected suite.sb3")
    else:
        print("scratch-parser not found; skipped")
    problems.extend(compile_cli_aliases())
    problems.extend(compile_ignored())
    problems.extend(compile_loop_tests())
    problems.extend(compile_images())
    problems.extend(compile_language())
    problems.extend(compile_decomp())
    problems.extend(compile_player())
    problems.extend(compile_rejects())
    if problems:
        print("FAILED")
        for item in problems:
            print(item)
        return 1
    print("compile gate passed")
    problems.extend(run_suites_on_scratch())
    if problems:
        print("FAILED")
        for item in problems:
            print(item)
        print("A row in 'failed tests' starts with the group in tests/project/suite.py, then the check name.")
        return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
