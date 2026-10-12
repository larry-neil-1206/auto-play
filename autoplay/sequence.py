"""Run emulate steps, repeating until Escape is pressed."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from autoplay.emulator import move_pointer, press_chord, scroll_vertical
from autoplay.win32 import GetAsyncKeyState

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


def run_step(step: dict[str, Any]) -> None:
    kind = step.get("type")
    if kind == "key":
        press_chord(str(step["keys"]), hold_ms=int(step.get("hold_ms", 40)))
    elif kind == "move":
        move_pointer(
            int(step["x"]),
            int(step["y"]),
            absolute=bool(step.get("absolute", True)),
        )
    elif kind == "scroll":
        scroll_vertical(int(step.get("notches", step.get("amount", -1))))
    elif kind == "sleep":
        ms = step.get("ms", step.get("milliseconds", 0))
        sleep_until_escape(float(ms) / 1000)
    else:
        raise ValueError(f"Unknown step type: {kind!r}")


def load_sequence(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
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
