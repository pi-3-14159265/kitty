# Kitty

Kitty compiles Python into Scratch 3 projects. It reads Kitty Python source and writes `.sb3` files; scripts are compiled, not interpreted by Python.

```bash
python comp.py script.py
python comp.py stage.py cat.py -o game.sb3
python comp.py folder/
```

## Documentation

The full documentation is maintained in [`docs/`](docs/README.md), organized as a set of focused pages:

- [Getting started](docs/getting-started.md)
- [Scripts and top-level behavior](docs/scripts.md)
- [Values and math](docs/values-and-math.md)
- [Choices and loops](docs/choices-and-loops.md)
- [Lists](docs/lists.md) and [dictionaries](docs/dictionaries.md)
- [Functions](docs/functions.md)
- [Sprites](docs/sprites.md)
- [Complete reference](docs/reference.md)

## Quick example

```python
import kitty

score = 0
kitty.say("Hello world!")
kitty.move(10)

@kitty.green_flag
def start():
    kitty.say("Started")
```

## Development

```bash
python tests/run.py
python comp.py tests/project -o tests/suite.sb3
```

The test suite compiles the project, validates the generated Scratch JSON with an optional local parser, and checks compiler rejection cases.
