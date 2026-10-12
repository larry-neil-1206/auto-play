"""High-level keyboard and mouse event emulation for the foreground window."""

from __future__ import annotations

import time

from autoplay.keys import EXTENDED_VKS, parse_chord
from autoplay.win32 import (
    INPUT,
    INPUT_KEYBOARD,
    INPUT_MOUSE,
    KEYBDINPUT,
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    MAPVK_VK_TO_VSC,
    MOUSEEVENTF_ABSOLUTE,
    MOUSEEVENTF_MOVE,
    MOUSEEVENTF_VIRTUALDESK,
    MOUSEEVENTF_WHEEL,
    MOUSEINPUT,
    POINT,
    SM_CXVIRTUALSCREEN,
    SM_CYVIRTUALSCREEN,
    SM_XVIRTUALSCREEN,
    SM_YVIRTUALSCREEN,
    WHEEL_DELTA,
    GetCursorPos,
    GetSystemMetrics,
    INPUTUNION,
    MapVirtualKeyW,
    send_inputs,
)


def _key_event(vk: int, up: bool) -> INPUT:
    scan = MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    flags = KEYEVENTF_SCANCODE
    if vk in EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    if up:
        flags |= KEYEVENTF_KEYUP
    return INPUT(
        type=INPUT_KEYBOARD,
        union=INPUTUNION(
            ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        ),
    )


def press_chord(chord: str, hold_ms: int = 40) -> None:
    """Hold modifiers, tap the last key, then release (e.g. ctrl+tab)."""
    codes = parse_chord(chord)
    *modifiers, trigger = codes
    send_inputs([_key_event(vk, up=False) for vk in modifiers])
    send_inputs([_key_event(trigger, up=False)])
    time.sleep(max(hold_ms, 0) / 1000)
    send_inputs([_key_event(trigger, up=True)])
    send_inputs([_key_event(vk, up=True) for vk in reversed(modifiers)])


def _virtual_screen() -> tuple[int, int, int, int]:
    left = GetSystemMetrics(SM_XVIRTUALSCREEN)
    top = GetSystemMetrics(SM_YVIRTUALSCREEN)
    width = GetSystemMetrics(SM_CXVIRTUALSCREEN)
    height = GetSystemMetrics(SM_CYVIRTUALSCREEN)
    if width <= 1 or height <= 1:
        raise RuntimeError("Could not read virtual screen size")
    return left, top, width, height


def _to_absolute(x: int, y: int) -> tuple[int, int]:
    left, top, width, height = _virtual_screen()
    abs_x = round((x - left) * 65535 / (width - 1))
    abs_y = round((y - top) * 65535 / (height - 1))
    return abs_x, abs_y


def cursor_position() -> tuple[int, int]:
    point = POINT()
    if not GetCursorPos(point):
        raise OSError("GetCursorPos failed")
    return point.x, point.y


def move_pointer(x: int, y: int, *, absolute: bool = True) -> None:
    """Move the mouse. Absolute uses screen pixels; relative uses pixel deltas."""
    if absolute:
        dx, dy = _to_absolute(x, y)
        flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
    else:
        dx, dy = x, y
        flags = MOUSEEVENTF_MOVE
    send_inputs(
        [
            INPUT(
                type=INPUT_MOUSE,
                union=INPUTUNION(
                    mi=MOUSEINPUT(
                        dx=dx,
                        dy=dy,
                        mouseData=0,
                        dwFlags=flags,
                        time=0,
                        dwExtraInfo=0,
                    )
                ),
            )
        ]
    )


def scroll_vertical(notches: int) -> None:
    """Scroll the wheel. Positive is up, negative is down. One notch is WHEEL_DELTA (120)."""
    if notches == 0:
        return
    delta = notches * WHEEL_DELTA
    send_inputs(
        [
            INPUT(
                type=INPUT_MOUSE,
                union=INPUTUNION(
                    mi=MOUSEINPUT(
                        dx=0,
                        dy=0,
                        mouseData=delta & 0xFFFFFFFF,
                        dwFlags=MOUSEEVENTF_WHEEL,
                        time=0,
                        dwExtraInfo=0,
                    )
                ),
            )
        ]
    )
