# Play a project: kitty run

`kitty run` plays a Scratch `.sb3` file in your web browser. The browser is
all it needs: Scratch's engine comes inside Kitty, so there is no Node.js, no
git, no Scratch account, no upload, and no internet connection.

```bash
kitty build game.py
kitty run game.sb3
```

`kitty run` plays `.sb3` files only. Build Python with `kitty build` first.
Any `.sb3` works, including projects saved from the Scratch editor.

The command prints an address such as `http://127.0.0.1:52133/` and opens it.
The address only works on this computer. Press **Ctrl+C** in the terminal to
stop.

## The player

- **Start** runs the green flag. The big button on the stage does the same the first time.
- **Stop** stops every script.
- **Turbo** runs scripts as fast as they can go.
- The square button shows the stage full screen.

The project gets the keyboard, the mouse, and the touch screen. A sprite set
to be draggable, with `kitty.start_with(draggable=True)` or
`kitty.set_drag_mode("draggable")`, can be dragged. `kitty.ask` opens an
answer box under the stage. Variables and lists with `show=True` appear on the
stage. Sounds play, the pen draws, and Music extension blocks play.

## Verbose mode

```bash
kitty run game.sb3 --verbose
```

`--verbose` (or `-v`) prints what happens while the project plays:

```text
game.sb3: 5.6 KB
  Stage: 2 costumes, 0 sounds, 1 scripts, 6 blocks, 3 variables, 1 lists
  sprite Hero: 2 costumes, 1 sounds, 6 scripts, 105 blocks, 3 variables, 1 lists
  extensions: music
Playing game.sb3 at http://127.0.0.1:52133/
[server] GET /project.sb3 200 5.6 KB
[player] loaded game.sb3 in 356 ms: 2 sprites
[player] green flag clicked
[player] when green flag clicked: started 1 script
[player] when I receive [ping]: started 1 script
[player] Hero says: What is your name?
[player] answer: Ada
[player] every script has finished
```

- The first lines sum up the file: each sprite's costumes, sounds, scripts, and blocks, and the extensions it uses.
- `[server]` lines are the files the page loads.
- `[player]` lines come from the page: each hat block that starts scripts, what sprites say and think, questions and answers, the buttons you press, when every script has finished, and any warning or error.

A line that repeats is counted instead of printed again, and at most 40 lines a
second are printed.

## Reload when the file changes

```bash
kitty run game.sb3 --watch
```

With `--watch`, the page loads the `.sb3` again whenever it changes, and if
the project was running, starts it again. Leave it running, and build in
another terminal:

```bash
kitty build game.py
```

## Options

| Option | What it does |
| --- | --- |
| `-v`, `--verbose` | Print what the project and the player do. |
| `--watch` | Reload the project when the `.sb3` file changes. |
| `--port 8000` | Use this port. The default is any free port. |
| `--no-browser` | Print the address without opening a browser. |

## What the player cannot do

- Text to Speech and Translate need Scratch's online services, Video Sensing
  needs a camera feed, and hardware extensions such as micro:bit and LEGO need
  Scratch Link. The player has none of these.
- Cloud variables stay on this computer.
- `kitty.loudness()` needs the microphone. The browser asks first, and
  loudness is -1 until you allow it.
- A key pressed again while its `@kitty.when_key` script is still running is
  skipped, as in Scratch.

## The Scratch engine

The player runs Scratch's own engine: scratch-vm, scratch-render,
scratch-storage, scratch-svg-renderer, and scratch-audio, by the Massachusetts
Institute of Technology. Kitty bundles the last releases under the BSD-3-Clause
license, from November 2024. Their licenses and the Scratch trademark notice
are in `kitty_player/vendor/licenses/`. The Scratch name, logo, and Scratch
Cat are trademarks of MIT and are not covered by those licenses.
