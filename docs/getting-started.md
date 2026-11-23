# Getting started

Create a Python source file, compile it with `comp.py`, and open the resulting
`.sb3` file in Scratch.

## What you need

- Python installed on your computer
- A Scratch 3 account or Scratch 3 editor
- The Kitty project folder

Kitty does not require third-party packages for compiled Scratch code.
Supported imports are `kitty` and `math`; use `@ignore` for a
Python-only helper that uses another library.

## Step 1: create `cat.py`

Create a plain text file named `cat.py` in the Kitty folder:

```python
import kitty

@kitty.green_flag
def start():
    kitty.say("Hello!")
    kitty.move(10)
```

## Step 2: compile it

Run this command in a terminal opened in the Kitty folder:

```bash
python comp.py cat.py
```

On success, Kitty prints the output path and creates `cat.sb3` beside
`cat.py`.

Open `cat.sb3` in Scratch. If you open it on the Scratch website, use
**File > Load from your computer**. Then click the green flag.

## Step 3: add a score

Variables start near the top of the file:

```python
import kitty

score = 0

@kitty.green_flag
def start():
    global score
    score += 1
    kitty.say(score)
```

The `global score` line is needed only inside a function that changes a
sprite variable. A function that only reads `score` does not need `global`.

## Compile one or more files

```bash
python comp.py script.py
python comp.py cat.py mouse.py
python comp.py cat.py mouse.py -o game.sb3
python comp.py folder/
```

- One script: output is `<script-name>.sb3` beside that script.
- Multiple scripts: output is `project.sb3`.
- `-o` or `--output`: choose a different `.sb3` name.
- A directory: compile `.py` files directly inside it.

The directory list does not search subfolders. It skips `comp.py`,
`kitty.py`, and `decomp.py`.

If there are no eligible Python files, the compiler stops with an error.
If no stage is provided, Kitty creates a white `backdrop1` stage.
An existing output file is replaced.

## Turn a Scratch project back into text

```bash
python decomp.py game.sb3
python decomp.py game.sb3 output_folder
```

The decompiler expects a Scratch `.sb3` ZIP file containing `project.json`.
It creates folders for the stage and sprites. Each folder contains
`script.txt`, costumes, and sounds. The top folder contains `project.txt`.

With no output folder, `game.sb3` becomes `game/`. If `game/` is already a
file, Kitty instead uses `game_decompiled/`.

## Common first mistakes

### I get “no Python scripts”

Check that the folder has a `.py` file directly inside it. Kitty does not scan
nested folders.

### Scratch does not open the file

Make sure the compiler created a `.sb3` file, then use Scratch’s
**Load from your computer** option.

### I get an unknown name

A name must be created before it is used:

```python
score = 0
kitty.say(score)
```

### The program reports that a Python import cannot be compiled

Keep `kitty` and `math` imports in compiled code. Put code that uses another
library in an ignored Python-only function:

```python
import numpy

@ignore
def numpyFunc():
    return numpy.mean([1, 2])
```

Kitty warns that `numpy` cannot be compiled. The function is omitted from the
Scratch project and must not be called from the compiled part of the script.
