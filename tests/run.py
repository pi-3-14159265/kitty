"""Compile the Scratch suite and the cases that must be rejected.

    python tests/run.py

Open tests/suite.sb3 in Scratch, click the green flag on the suite sprite,
and wait until it says failed 0. A failure says FAIL and a short name.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
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
    ("stage", 'kitty.backdrop("wide.png", name="field")', {"name": "field", "rotationCenterX": 50, "rotationCenterY": 30}),
]

# (declaration, text that must be in the error)
IMAGE_REJECTS = [
    ('kitty.costume("cat.gif")', "svg, png, or jpg"),
    ('kitty.costume("wide.png", resolution=3)', "resolution is 1 or 2"),
    ('kitty.costume("box.svg", resolution=2)', "resolution is for png and jpg"),
    ('kitty.sound("ping.wav", resolution=2)', "resolution belongs on a costume"),
]

# (declaration, text that must be in a warning, or None for no warning)
IMAGE_WARNINGS = [
    ('kitty.costume("huge.png")', "500 x 10, bigger than the 480 x 360 stage"),
    ('kitty.costume("huge.png", resolution=2)', None),
    ('kitty.costume("bare.svg")', "no viewBox"),
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
    problems.extend(compile_rejects())
    if problems:
        print("FAILED")
        for item in problems:
            print(item)
        return 1
    print("compile gate passed")
    print("Open tests/suite.sb3 in Scratch and click the green flag.")
    print("Wait for failed 0. Names that failed stay in the list 'failed tests'.")
    print("Each row starts with the group in tests/project/suite.py, then the check name.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
