"""Unified command-line interface for installed Kitty builds."""

from __future__ import annotations

import argparse


def main(argv=None):
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

    decompile = subparsers.add_parser("decompile", help="decompile .sb3 into text and assets")
    decompile.add_argument("source", help="Scratch .sb3 file")
    decompile.add_argument("directory", nargs="?", help="output directory")

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
