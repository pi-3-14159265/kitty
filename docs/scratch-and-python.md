# Python syntax and Scratch API

Use Python syntax for program structure. Use the `kitty` module for Scratch
operations that Python does not define.

## Events

| Python or Kitty syntax | Scratch operation |
| --- | --- |
| `@kitty.green_flag` | when green flag clicked |
| `@kitty.when_key("space")` | when [space] key pressed |
| `@kitty.when_clicked` | when this sprite clicked |
| `@kitty.when_backdrop("name")` | when backdrop switches to [name] |
| `@kitty.when_receive("message")` | when I receive [message] |
| `kitty.broadcast("message")` | broadcast [message] |

## Movement

| Scratch | Kitty |
| --- | --- |
| move 10 steps | `kitty.move(10)` |
| turn right 15 degrees | `kitty.turn_right(15)` |
| go to x: 0 y: 0 | `kitty.go_to_xy(0, 0)` |
| change x by 10 | `kitty.change_x(10)` |
| set x to 0 | `kitty.set_x(0)` |

## Looks and sound

| Scratch | Kitty |
| --- | --- |
| say Hello! | `kitty.say("Hello!")` |
| say Hello! for 2 seconds | `kitty.say_for("Hello!", 2)` |
| next costume | `kitty.next_costume()` |
| switch backdrop to [name] | `kitty.switch_backdrop("name")` |
| play sound [name] until done | `kitty.play_until_done("name")` |

## Control

| Scratch | Kitty |
| --- | --- |
| repeat 10 | `for _ in range(10):` |
| repeat until [condition] | `while not condition:` |
| forever | `while True:` |
| wait 1 second | `kitty.wait(1)` |
| stop [this script] | `kitty.stop("this script")` |

## Variables and lists

| Scratch | Kitty |
| --- | --- |
| set [score] to 0 | `score = 0` |
| change [score] by 1 | `score += 1` |
| add [thing] to [items] | `items.append("thing")` |
| delete item 1 of [items] | `items.pop(0)` |
| item 1 of [items] | `items[0]` |
| length of [items] | `len(items)` |

Scratch list item blocks use 1 as the first item. Kitty Python indexes start
at `0`. To read the first Kitty list item, use `items[0]`.

## Important differences

- Python text must be in quotes: `"Hello"`.
- The equal sign means assignment: `score = 0`.
- Double equals compares values: `score == 10`.
- Indentation is important. Put four spaces before code inside `if`, `for`,
  `while`, and `def` blocks.
- Scratch colors and menu choices are still used in Kitty calls.
- Kitty is a Scratch compiler. It does not run ordinary Python libraries or
  local files when the `.sb3` is opened.
