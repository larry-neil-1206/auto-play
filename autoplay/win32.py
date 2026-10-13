"""Minimal Win32 bindings for SendInput-based keyboard and mouse injection."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

MAPVK_VK_TO_VSC = 0
WHEEL_DELTA = 120

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUTUNION(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = (("type", wintypes.DWORD), ("union", INPUTUNION))


class POINT(ctypes.Structure):
    _fields_ = (("x", wintypes.LONG), ("y", wintypes.LONG))


SendInput = user32.SendInput
SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = wintypes.UINT

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.argtypes = ()
GetForegroundWindow.restype = wintypes.HWND

GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextLengthW.argtypes = (wintypes.HWND,)
GetWindowTextLengthW.restype = ctypes.c_int

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
GetWindowTextW.restype = ctypes.c_int

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
GetWindowThreadProcessId.restype = wintypes.DWORD

MapVirtualKeyW = user32.MapVirtualKeyW
MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
MapVirtualKeyW.restype = wintypes.UINT

GetSystemMetrics = user32.GetSystemMetrics
GetSystemMetrics.argtypes = (ctypes.c_int,)
GetSystemMetrics.restype = ctypes.c_int

GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
GetCursorPos.restype = wintypes.BOOL

GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = (ctypes.c_int,)
GetAsyncKeyState.restype = wintypes.SHORT

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
OpenProcess.restype = wintypes.HANDLE

QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
QueryFullProcessImageNameW.argtypes = (
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
)
QueryFullProcessImageNameW.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = (wintypes.HANDLE,)
CloseHandle.restype = wintypes.BOOL


def get_foreground_window_info() -> tuple[str, str]:
    """Return the foreground window's process executable name and title."""
    hwnd = GetForegroundWindow()
    if not hwnd:
        return "", ""

    title_length = GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(title_length + 1)
    GetWindowTextW(hwnd, title_buffer, len(title_buffer))

    process_id = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    process_name = ""
    process_handle = OpenProcess(0x1000, False, process_id.value)
    if process_handle:
        try:
            image_buffer = ctypes.create_unicode_buffer(32768)
            image_length = wintypes.DWORD(len(image_buffer))
            if QueryFullProcessImageNameW(
                process_handle, 0, image_buffer, ctypes.byref(image_length)
            ):
                process_name = image_buffer.value.rsplit("\\", 1)[-1]
        finally:
            CloseHandle(process_handle)

    return process_name, title_buffer.value


def send_inputs(events: list[INPUT]) -> int:
    if not events:
        return 0
    array = (INPUT * len(events))(*events)
    sent = SendInput(len(events), array, ctypes.sizeof(INPUT))
    if sent != len(events):
        raise ctypes.WinError(ctypes.get_last_error())
    return sent
