"""Compile the Scratch suite and the cases that must be rejected.

    python tests/run.py

Open tests/suite.sb3 in Scratch, click the green flag on the suite sprite,
and wait until it says failed 0. A failure says FAIL and a short name.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
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
