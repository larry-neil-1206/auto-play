# auto-play

Python 3 tool that **emulates keyboard and mouse events on Windows** (Ctrl+Tab, pointer move, wheel scroll). It uses the Win32 `SendInput` API. There is no installer and no `.exe` — you run it with Python.

Events go to whichever window is **in the foreground**. Commands **repeat forever** until you press **Escape**.

## Requirements

- Windows
- Python 3 (3.10 or newer is fine)

No `pip install` is required. The project only uses the standard library.

## Start here

Open a terminal in this project folder (`auto-play`).

Show all commands:

```bash
python -m autoplay --help
```

Print the current mouse position (screen pixels):

```bash
python -m autoplay position
```

That command is a good sanity check. If it prints two numbers, Python and the Win32 bindings are working.

## Repeat until Escape

Each emit command waits **2 seconds** first so you can click the window that should receive the events. Then it keeps sending the event every **0.5 seconds** until you press **Escape**.

You do not need the terminal to stay focused. Escape is watched for the whole session.

**Key chord** (Ctrl+Tab):

```bash
python -m autoplay key ctrl+tab
```

Other chords use `+` between keys, for example `ctrl+shift+t` or `alt+tab`.

**Move the pointer** to an absolute screen position (repeats that move):

```bash
python -m autoplay move 400 300
```

**Move the pointer** by a relative pixel offset each time:

```bash
python -m autoplay move 20 -10 --relative
```

**Scroll the mouse wheel**. Negative values scroll **down**:

```bash
python -m autoplay scroll -3
```

### Options

| Flag | Meaning |
| --- | --- |
| `--delay 2` | Seconds to wait before the first event so you can focus a window |
| `--interval 0.5` | Seconds between repeats |
| `--once` | Send the event one time, then exit |
| `--delay 0` | Skip the countdown |

Examples:

```bash
python -m autoplay key ctrl+tab --interval 1
python -m autoplay key ctrl+tab --once
python -m autoplay scroll -3 --delay 0 --interval 0.2
```

## Play a sequence

There is a sample file at `sequences/example.json`. It sends Ctrl+Tab, moves the pointer, then scrolls down, and repeats until Escape:

```bash
python -m autoplay run sequences/example.json
```

Run the file once:

```bash
python -m autoplay run sequences/example.json --once
```

You can copy that JSON and change the steps. Supported step types:

```json
{ "type": "key", "keys": "ctrl+tab", "hold_ms": 40 }
{ "type": "move", "x": { "min": -80, "max": 80 }, "y": { "min": -80, "max": 80 }, "absolute": false }
{ "type": "scroll", "notches": -3 }
{ "type": "sleep", "ms": 400 }
```

Optional sequence fields:

- `"delay_ms": 400` — pause between loops (override with `--interval`)
- `"loops": 5` — stop after five loops (Escape still quits early). Omit this field to run forever.

## Use it from Python

```python
from autoplay import press_chord, move_pointer, scroll_vertical

press_chord("ctrl+tab")
move_pointer(400, 300)
scroll_vertical(-3)
```

## Things to know

- Events are delivered to the **foreground window**, not to a process you name.
- A normal (non-admin) Python process generally cannot inject into an **elevated** window.
- Some games and apps that read raw input ignore synthetic `SendInput` events.
- Relative mouse moves can be affected by Windows pointer acceleration, so a delta of `5` pixels may not move exactly five pixels.
