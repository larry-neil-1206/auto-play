"""Virtual-key names used by chord strings like ctrl+tab."""

from __future__ import annotations

VK_CODES: dict[str, int] = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "caps": 0x14,
    "capslock": 0x14,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "ins": 0x2D,
    "delete": 0x2E,
    "del": 0x2E,
    "win": 0x5B,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "apps": 0x5D,
    "lshift": 0xA0,
    "rshift": 0xA1,
    "lctrl": 0xA2,
    "rctrl": 0xA3,
    "lalt": 0xA4,
    "ralt": 0xA5,
    "plus": 0xBB,
    "comma": 0xBC,
    "minus": 0xBD,
    "period": 0xBE,
}

# Arrow keys, Delete, Insert, Home/End, Page Up/Down, and right modifiers.
EXTENDED_VKS = {
    0x21,
    0x22,
    0x23,
    0x24,
    0x25,
    0x26,
    0x27,
    0x28,
    0x2D,
    0x2E,
    0x5B,
    0x5C,
    0x5D,
    0xA3,
    0xA5,
}

for _index in range(1, 25):
    VK_CODES[f"f{_index}"] = 0x6F + _index  # F1 = 0x70

for _digit in "0123456789":
    VK_CODES[_digit] = ord(_digit)

for _letter in "abcdefghijklmnopqrstuvwxyz":
    VK_CODES[_letter] = ord(_letter.upper())


def parse_chord(chord: str) -> list[int]:
    """Parse 'ctrl+tab' or 'ctrl+shift+t' into virtual-key codes, modifiers first."""
    parts = [part.strip().lower() for part in chord.replace("-", "+").split("+") if part.strip()]
    if not parts:
        raise ValueError("Empty key chord")

    codes: list[int] = []
    for part in parts:
        if part not in VK_CODES:
            raise ValueError(f"Unknown key name: {part!r}")
        codes.append(VK_CODES[part])
    return codes
