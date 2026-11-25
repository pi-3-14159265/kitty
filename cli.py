"""Unified command-line interface for installed Kitty builds."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_windows_launchers():
    if os.name != "nt":
        return

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return

    launcher_dir = Path(local_app_data) / "Microsoft" / "WindowsApps"
    if not launcher_dir.is_dir():
        return

    python = str(Path(sys.executable)).replace('"', '""')
    launchers = {
        "kitty.cmd": '@echo off\r\n"%s" -m kitty %%*\r\n' % python,
        "kitty-build.cmd": '@echo off\r\n"%s" -m comp %%*\r\n' % python,
        "kitty-decomp.cmd": '@echo off\r\n"%s" -m decomp %%*\r\n' % python,
    }
    for name, content in launchers.items():
        target = launcher_dir / name
        try:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                target.write_text(content, encoding="utf-8", newline="")
        except OSError:
            return


def main(argv=None):
    _ensure_windows_launchers()
    parser = argparse.ArgumentParser(
        prog="kitty",
        description="Compile and decompile Kitty/Scratch projects",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="print the Kitty version")

    build = subparsers.add_parser(
        "build",
        aliases=["compile", "comp"],
        help="compile Python source into .sb3",
    )
    build.add_argument("scripts", nargs="+", help="Python files or a directory")
    build.add_argument("-o", "--output", help="output .sb3 path")

    decompile = subparsers.add_parser(
        "decomp",
        aliases=["decompile"],
        help="decompile .sb3 into a Kitty Python project folder",
    )
    decompile.add_argument("source", help="Scratch .sb3 file")
    decompile.add_argument("directory", nargs="?", help="new or empty output folder")

    args = parser.parse_args(argv)
    if args.command == "version":
        import kitty
        print(kitty.__version__)
        return 0
    if args.command in {"build", "compile", "comp"}:
        from comp import main as build_main
        return build_main(["--output", args.output, *args.scripts]) if args.output else build_main(args.scripts)

    from decomp import main as decompile_main
    return decompile_main(args.source, args.directory)


if __name__ == "__main__":
    raise SystemExit(main())
