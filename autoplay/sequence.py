"""Run emulate steps, repeating until Escape is pressed."""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable

from autoplay.emulator import move_pointer, press_chord, scroll_vertical
from autoplay.win32 import GetAsyncKeyState, get_foreground_window_info

VK_ESCAPE = 0x1B


class SequenceAborted(RuntimeError):
    pass


def escape_is_down() -> bool:
    return bool(GetAsyncKeyState(VK_ESCAPE) & 0x8000)


def arm_escape_watch() -> None:
    """Ignore an Escape that was already held, then watch for a new press."""
    GetAsyncKeyState(VK_ESCAPE)
    while escape_is_down():
        time.sleep(0.02)


def raise_if_escape() -> None:
    if escape_is_down():
        raise SequenceAborted("Stopped because Escape was pressed")


def sleep_until_escape(seconds: float) -> None:
    deadline = time.monotonic() + max(seconds, 0)
    while True:
        raise_if_escape()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.03, remaining))


def run_until_escape(
    tick: Callable[[], None],
    *,
    interval: float,
    loops: int = 0,
    on_loop: Callable[[int], None] | None = None,
) -> None:
    """Call tick() forever (or `loops` times). Stop when Escape is pressed."""
    arm_escape_watch()
    iteration = 0
    while True:
        raise_if_escape()
        iteration += 1
        if on_loop:
            on_loop(iteration)
        tick()
        if loops and iteration >= loops:
            return
        sleep_until_escape(interval)


def _int_or_range(value: Any, name: str, *, nonzero: bool = False) -> int:
    """Accept a fixed int or a random range: {\"min\": -3, \"max\": 3} or [-3, 3]."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{name} must be a number or a min/max range")
    if isinstance(value, (int, float)):
        chosen = int(value)
        if nonzero and chosen == 0:
            raise ValueError(f"{name} cannot be 0")
        return chosen
    if isinstance(value, dict):
        low, high = int(value["min"]), int(value["max"])
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        low, high = int(value[0]), int(value[1])
    else:
        raise ValueError(f"{name} must be a number or a min/max range")
    if low > high:
        low, high = high, low
    if nonzero and low <= 0 <= high:
        choices = [n for n in range(low, high + 1) if n != 0]
        if not choices:
            raise ValueError(f"{name} range must include a non-zero value")
        return random.choice(choices)
    return random.randint(low, high)


def press_random_discord_navigation() -> bool:
    process_name, title = get_foreground_window_info()
    if process_name.casefold() != "chrome.exe" or "discord" not in title.casefold():
        return False
    press_chord(f"ctrl+alt+{random.choice(('up', 'down'))}")
    return True


def run_step(step: dict[str, Any]) -> None:
    kind = step.get("type")
    if kind == "key":
        repeats = _int_or_range(step.get("repeat", 1), "repeat")
        if repeats < 1:
            raise ValueError("repeat must be at least 1")
        for _ in range(repeats):
            press_chord(str(step["keys"]), hold_ms=int(step.get("hold_ms", 40)))
    elif kind == "move":
        move_pointer(
            _int_or_range(step["x"], "x"),
            _int_or_range(step["y"], "y"),
            absolute=bool(step.get("absolute", True)),
        )
    elif kind == "scroll":
        notches = step.get("notches", step.get("amount", -1))
        scroll_vertical(_int_or_range(notches, "notches", nonzero=True))
    elif kind == "sleep":
        ms = step.get("ms", step.get("milliseconds", 0))
        sleep_until_escape(float(ms) / 1000)
    elif kind == "discord_navigation":
        sleep_until_escape(float(step.get("settle_ms", 100)) / 1000)
        press_random_discord_navigation()
    else:
        raise ValueError(f"Unknown step type: {kind!r}")


def load_sequence(path: str | Path) -> dict[str, Any]:
    sequence_path = Path(path)
    if not sequence_path.is_file():
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root is not None:
            bundled_path = Path(bundle_root) / sequence_path
            if bundled_path.is_file():
                sequence_path = bundled_path
    data = json.loads(sequence_path.read_text(encoding="utf-8"))
    if "steps" not in data or not isinstance(data["steps"], list):
        raise ValueError("Sequence JSON must contain a 'steps' array")
    return data


def _sequence_loops(data: dict[str, Any], override: int | None) -> int:
    if override is not None:
        return override
    if "loops" in data:
        return int(data["loops"])
    if data.get("loop") is False:
        return 1
    return 0


def run_sequence(
    data: dict[str, Any],
    *,
    loops: int | None = None,
    interval: float | None = None,
    on_loop: Callable[[int], None] | None = None,
) -> None:
    repeat = _sequence_loops(data, loops)
    if interval is None:
        delay_ms = int(data.get("delay_ms", 400))
        gap = delay_ms / 1000
    else:
        gap = interval

    def tick() -> None:
        for step in data["steps"]:
            raise_if_escape()
            run_step(step)

    run_until_escape(tick, interval=gap, loops=repeat, on_loop=on_loop)
