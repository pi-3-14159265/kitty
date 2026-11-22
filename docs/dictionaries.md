# Dictionaries

A dictionary stores pairs of names and values. The name side is called a key,
and the other side is called a value.

## First dictionary

```python
import kitty

scores = {"Ada": 3, "Bea": 5}

@kitty.green_flag
def start():
    kitty.say(scores["Ada"])
```

A dictionary is two Scratch lists, one for keys and one for values. Keys and values are numbers or text.

```python
scores = {"ada": 3, "bea": 5}
kitty.say(scores["ada"])
kitty.say(scores[name])
scores["ada"] = 9
scores[name] = 4
scores[name] += 1

if "bea" in scores:
    kitty.say(len(scores))

for name in scores:
    kitty.say(scores[name])

kitty.say(scores.get("nope", 0))
scores.update({"bea": 4})
gone = scores.pop("ada")
scores.clear()
```

`scores["ada"]` reads the value. Assigning a missing key adds it. `get` uses the second value when the key is missing. `update` adds those pairs and keeps the keys that are already there. `pop` reads a value and removes that key. `clear` deletes every key and value. `{}` starts an empty dictionary.

A dictionary name points at one dictionary. `other = scores` points both names at that dictionary.

```python
scores = {"ada": 3}
other = scores
other["ada"] = 9
kitty.say(scores["ada"])
```

`other["ada"] = 9` changes that dictionary, so `scores["ada"]` is `9`.

`scores = {}` points `scores` at a new dictionary. `other` still has the old keys and values.

`kitty.dict` is the same declaration when you want a Scratch name, monitors, or a shared dictionary. The lists are named `name keys` and `name values`.
