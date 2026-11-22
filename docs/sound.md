## Sound

### kitty.play_until_done

Play a sound and wait until it finishes.

**sound:** the sound's name.

```python
kitty.play_until_done("meow")
```

### kitty.start_sound

Start a sound and keep going.

**sound:** the sound's name.

```python
kitty.start_sound("meow")
```

### kitty.stop_all_sounds

Stop every sound.

```python
kitty.stop_all_sounds()
```

### kitty.change_sound_effect

Change a sound effect.

**effect:** `pitch` or `pan left/right`.

**value:** how much to add.

```python
kitty.change_sound_effect("pitch", 10)
```

### kitty.set_sound_effect

Set a sound effect.

**effect:** `pitch` or `pan left/right`.

**value:** the new amount.

```python
kitty.set_sound_effect("pan left/right", 0)
```

### kitty.clear_sound_effects

Clear every sound effect.

```python
kitty.clear_sound_effects()
```

### kitty.change_volume

Change the volume.

**amount:** how much to add.

```python
kitty.change_volume(-10)
```

### kitty.set_volume

Set the volume. `100` is full.

**percent:** the volume.

```python
kitty.set_volume(50)
```

### kitty.volume

The volume.

```python
kitty.say(kitty.volume())
```
