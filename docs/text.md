## Text

Read text the way Python reads it. `text[0]` is the first letter. `text[1:4]` is a slice. `kitty.letter` is the Scratch block, and that block still starts at 1.

```python
word = "Hello"
kitty.say(word[0])
kitty.say(word[1:4])
kitty.say(word.upper())
kitty.say("  hi ".strip())
kitty.say("a-b".split("-")[0])
kitty.say("-".join(["a", "b"]))
kitty.say("cater".replace("cat", "dog"))
kitty.say("cater".find("at"))
kitty.say("banana".count("a"))
kitty.say(word.startswith("He"))
kitty.say(word.endswith("o"))
kitty.say("12".isdigit())
kitty.say("ab".isalpha())
kitty.say(f"n={score}")
```

`lower`, `lstrip`, and `rstrip` are there too. `strip` removes spaces. `find` returns -1 when the text is missing. An f-string joins the pieces. A format spec such as `f"{n:.2f}"` is not supported.
