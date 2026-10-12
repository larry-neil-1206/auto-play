"""Command-line entry for looping keyboard and mouse emulation."""

from __future__ import annotations

import argparse
import sys

from autoplay.emulator import cursor_position, move_pointer, press_chord, scroll_vertical
from autoplay.sequence import SequenceAborted, load_sequence, run_sequence, run_until_escape, sleep_until_escape


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait so you can focus the target window (default: 2)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Seconds to wait between repeats (default: 0.5, or delay_ms in a sequence file)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fire the event once instead of repeating until Escape",
    )


def _countdown(seconds: float) -> None:
    if seconds <= 0:
        return
    print(
        f"Starting in {seconds:g}s — focus the target window. "
        "Press Escape at any time to quit."
    )
    sleep_until_escape(seconds)


def _repeat_count(once: bool) -> int:
    return 1 if once else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m autoplay",
        description="Emulate keyboard and mouse events on Windows via SendInput. "
        "Commands repeat until you press Escape (unless --once).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    key = sub.add_parser("key", help="Send a key chord, e.g. ctrl+tab")
    key.add_argument("chord", help="Keys joined by +, e.g. ctrl+tab or ctrl+shift+t")
    key.add_argument("--hold-ms", type=int, default=40, help="How long to hold the final key")
    _add_common(key)

    move = sub.add_parser("move", help="Move the mouse pointer")
    move.add_argument("x", type=int, help="X in screen pixels, or delta if --relative")
    move.add_argument("y", type=int, help="Y in screen pixels, or delta if --relative")
    move.add_argument("--relative", action="store_true", help="Treat x/y as pixel offsets")
    _add_common(move)

    scroll = sub.add_parser("scroll", help="Vertical mouse wheel. Negative is down.")
    scroll.add_argument("notches", type=int, help="Wheel notches, e.g. -3 for three downs")
    _add_common(scroll)

    pos = sub.add_parser("position", help="Print the current cursor position")

    run = sub.add_parser("run", help="Play a JSON sequence of events")
    run.add_argument("path", help="Path to a sequence JSON file")
    _add_common(run)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "position":
        x, y = cursor_position()
        print(f"{x} {y}")
        return 0

    try:
        _countdown(args.delay)
        loops = _repeat_count(args.once)
        if not args.once:
            print("Repeating until you press Escape.", file=sys.stderr)

        gap = 0.5 if args.interval is None else args.interval

        if args.command == "key":
            run_until_escape(
                lambda: press_chord(args.chord, hold_ms=args.hold_ms),
                interval=gap,
                loops=loops,
            )
        elif args.command == "move":
            run_until_escape(
                lambda: move_pointer(args.x, args.y, absolute=not args.relative),
                interval=gap,
                loops=loops,
            )
        elif args.command == "scroll":
            run_until_escape(
                lambda: scroll_vertical(args.notches),
                interval=gap,
                loops=loops,
            )
        elif args.command == "run":
            data = load_sequence(args.path)
            run_sequence(
                data,
                loops=loops or None,
                interval=args.interval,
            )
    except SequenceAborted as exc:
        print(exc, file=sys.stderr)
        return 0
    return 0
