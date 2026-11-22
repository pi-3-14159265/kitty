## try and except

`try` / `except` catches `raise` only. Scratch does not turn its own problems into exceptions. A bad index, a missing dictionary key, division by zero, and an unknown name do not jump into `except`. Write `raise` when you want the `except` block to run. `except` and `except Exception` both catch that `raise`. `except Exception as problem` stores the message in `problem`. `else` runs when nothing was raised. `finally` always runs.

```python
try:
    raise Exception("missing")
except Exception as problem:
    kitty.say(problem)
else:
    kitty.say("ok")
finally:
    kitty.say("done")
```
