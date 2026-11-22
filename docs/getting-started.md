## Compile

```bash
python comp.py script.py
python comp.py stage.py cat.py -o game.sb3
python comp.py folder/
```

One script becomes `<name>.sb3` next to that file. Several scripts default to
`project.sb3`. A directory uses the same rule after collecting its files: one
eligible file defaults to that file's `<name>.sb3`, while multiple files
default to `project.sb3`. A directory compiles every `.py` file in it except
`comp.py`, `kitty.py`, and `decomp.py`.

The directory scan is not recursive; only `.py` files directly inside the
directory are included. If a directory contains no eligible Python files,
compilation fails. If no stage is supplied, Kitty adds an empty stage with a
white `backdrop1`. The output directory is created when needed, and an
existing output archive is replaced.

Compilation errors are printed to standard error and the command exits with
status 1. The compiler only permits the `kitty` and `math` modules; other
imports are rejected. A project may contain only one stage.

```bash
python decomp.py game.sb3
python decomp.py game.sb3 output_folder
```

`decomp` writes the project back out as a folder. With no output folder, it
uses a folder beside the archive with the archive's extension removed
(`game.sb3` becomes `game/`). If that path is an existing file, it uses
`game_decompiled/` instead. Each target gets a directory containing
`script.txt` next to its costumes and sounds. The stage is the `Stage`
directory. `project.txt` sits at the top. The input must be a Scratch ZIP archive (normally named `.sb3`)
containing `project.json`; the filename extension itself is not validated.
