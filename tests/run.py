"""Compile the Scratch suite and the cases that must be rejected.

    python tests/run.py

Open tests/suite.sb3 in Scratch, click the green flag on the suite sprite,
and wait until it says failed 0. A failure says FAIL and a short name.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from comp import CompileError, comp

SUITE = ROOT / "tests" / "suite.sb3"
PROJECT = ROOT / "tests" / "project"
PARSER = Path(r"C:\Users\thaya\AppData\Local\Temp\scratchparse\check.js")
TMP = ROOT / "tests" / "_reject"

# Each snippet must fail to compile, and the message must contain the text.
REJECTS = [
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
