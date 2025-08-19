from __future__ import annotations

from ctypes import (
    POINTER,
    WINFUNCTYPE,
    Structure,
    Union,
    WinDLL,
    WinError,
    byref,
    c_ulonglong,
    create_unicode_buffer,
    get_last_error,
    sizeof,
    wintypes,
)
from typing import TYPE_CHECKING, cast

from automate.winterop.win32_constants import (
    CCHILDREN_TITLEBAR,
    INPUT_MOUSE,
    MAX_CHARS,
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
)

if TYPE_CHECKING:
    from collections.abc import Callable


_user32 = WinDLL("user32", use_last_error=True)


class TITLEBARINFO(Structure):
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-titlebarinfo

    typedef struct tagTITLEBARINFO {
        DWORD cbSize;
        RECT  rcTitleBar;
        DWORD rgstate[CCHILDREN_TITLEBAR + 1];
    } TITLEBARINFO, *PTITLEBARINFO, *LPTITLEBARINFO;
    """

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcTitleBar", wintypes.RECT),
        ("rgstate", wintypes.DWORD * (CCHILDREN_TITLEBAR + 1)),
    ]


_user32.GetLastActivePopup.argtypes = [wintypes.HWND]
_user32.GetLastActivePopup.restype = wintypes.HWND


def GetLastActivePopup(hwnd: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getlastactivepopup

    HWND GetLastActivePopup(
        [in] HWND hWnd
    );
    """
    return cast(int, _user32.GetLastActivePopup(hwnd))


_user32.GetTitleBarInfo.argtypes = [wintypes.HWND, POINTER(TITLEBARINFO)]
_user32.GetTitleBarInfo.restype = wintypes.BOOL


def GetTitleBarInfo(hwnd: int) -> TITLEBARINFO:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-gettitlebarinfo

    BOOL GetTitleBarInfo(
        [in]      HWND          hwnd,
        [in, out] PTITLEBARINFO pti
    );
    """
    ti = TITLEBARINFO()
    ti.cbSize = sizeof(ti)
    if not _user32.GetTitleBarInfo(hwnd, byref(ti)):
        raise WinError(get_last_error())
    return ti


_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL


def IsWindow(hwnd: int) -> bool:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindow
    """
    return bool(cast(int, _user32.IsWindow(hwnd)))


_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_user32.GetClassNameW.restype = wintypes.INT


def GetClassNameW(hwnd: int) -> str:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclassnamew
    """
    buffer = create_unicode_buffer(MAX_CHARS)
    name_length = cast(int, _user32.GetClassNameW(hwnd, buffer, MAX_CHARS))
    if name_length <= 0:
        return ""
    return cast(str, buffer.value)


_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, wintypes.LPDWORD]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def GetWindowThreadProcessId(hwnd: int) -> tuple[int, int]:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
    """
    pid = wintypes.DWORD()
    tid = cast(int, _user32.GetWindowThreadProcessId(hwnd, byref(pid)))
    if tid == 0:
        raise WinError(get_last_error())

    return tid, pid.value


_user32.GetWindowRect.argtypes = [wintypes.HWND, POINTER(wintypes.RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL


def GetWindowRect(hwnd: int) -> wintypes.RECT:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowrect
    """
    rect = wintypes.RECT()
    if _user32.GetWindowRect(hwnd, byref(rect)) == 0:
        raise WinError(get_last_error())

    return rect


_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND


def GetForegroundWindow() -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow
    """
    hwnd = cast(int, _user32.GetForegroundWindow())
    if hwnd == 0:
        raise ValueError(
            (
                "The result of 'GetForegroundWindow' is None. "
                "The foreground window can be NULL in certain circumstances, "
                "such as when a window is losing activation."
            )
        )
    return hwnd


_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL


def IsWindowVisible(hwnd: int) -> bool:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindowvisible
    """
    return cast(int, _user32.IsWindowVisible(hwnd)) != 0


_user32.IsWindowEnabled.argtypes = [wintypes.HWND]
_user32.IsWindowEnabled.restype = wintypes.BOOL


def IsWindowEnabled(hwnd: int) -> bool:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindowenabled
    """
    return cast(int, _user32.IsWindowEnabled(hwnd)) != 0


_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_user32.GetWindowTextW.restype = wintypes.INT


def GetWindowTextW(hwnd: int) -> str:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowtextw
    """
    buffer = create_unicode_buffer(MAX_CHARS)
    name_length = cast(int, _user32.GetWindowTextW(hwnd, buffer, MAX_CHARS))
    if name_length <= 0:
        return ""
    return cast(str, buffer.value)


_user32.GetParent.argtypes = [wintypes.HWND]
_user32.GetParent.restype = wintypes.HWND


def GetParent(hwnd: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getparent
    """
    return cast(int, _user32.GetParent(hwnd))


_user32.AttachThreadInput.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.BOOL,
]
_user32.AttachThreadInput.restype = wintypes.BOOL


def AttachThreadInput(idAttach: int, idAttachTo: int, fAttach: bool) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput
    """
    if _user32.AttachThreadInput(idAttach, idAttachTo, fAttach) == 0:
        raise WinError(get_last_error())


_user32.GetWindowLongW.argtypes = [wintypes.HWND, wintypes.INT]
_user32.GetWindowLongW.restype = wintypes.LONG


def GetWindowLongW(hwnd: int, nIndex: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowlongw
    """
    ok = cast(int, _user32.GetWindowLongW(hwnd, nIndex))
    err = get_last_error()
    if ok == 0 and err != 0:
        raise WinError(err)
    return ok


_user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetWindow.restype = wintypes.HWND


def GetWindow(hwnd: int, uCmd: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindow
    """
    res_hwnd = cast(int, _user32.GetWindow(hwnd, uCmd))
    if res_hwnd == 0:
        raise WinError(get_last_error())
    return res_hwnd


_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetAncestor.restype = wintypes.HWND


def GetAncestor(hwnd: int, gaFlags: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getancestor
    """
    anc_hwnd = cast(int, _user32.GetAncestor(hwnd, gaFlags))
    if anc_hwnd == 0:
        raise WinError(get_last_error())
    return anc_hwnd


_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL


def IsIconic(hwnd: int) -> bool:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-isiconic
    """
    return bool(cast(int, _user32.IsIconic(hwnd)))


_user32.IsZoomed.argtypes = [wintypes.HWND]
_user32.IsZoomed.restype = wintypes.BOOL


def IsZoomed(hwnd: int) -> bool:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iszoomed
    """
    return bool(cast(int, _user32.IsZoomed(hwnd)))


_user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    wintypes.INT,
    wintypes.INT,
    wintypes.INT,
    wintypes.INT,
    wintypes.UINT,
]
_user32.SetWindowPos.restype = wintypes.BOOL


def SetWindowPos(
    hwnd: int,
    hwndInsertAfter: int,
    X: int,
    Y: int,
    cx: int,
    cy: int,
    uFlags: int,
) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
    """
    if _user32.SetWindowPos(hwnd, hwndInsertAfter, X, Y, cx, cy, uFlags) == 0:
        raise WinError(get_last_error())


_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL


def SetForegroundWindow(hwnd: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
    """
    if _user32.SetForegroundWindow(hwnd) == 0:
        raise WinError(get_last_error())


_user32.ShowWindow.argtypes = [wintypes.HWND, wintypes.INT]
_user32.ShowWindow.restype = wintypes.BOOL


def ShowWindow(hwnd: int, nCmdShow: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
    """
    _user32.ShowWindow(hwnd, nCmdShow)


_EnumWindowsProc = WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_EnumWindowsProc, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL


def EnumWindows(callback: Callable[[int], bool]) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows
    """

    def _callback(hwnd: int, _: int) -> int:
        try:
            return 1 if callback(hwnd) else 0
        except Exception:
            return 1

    c_callback = _EnumWindowsProc(_callback)
    ok = cast(int, _user32.EnumWindows(c_callback, 0))
    err = get_last_error()
    if ok == 0 and err != 0:
        raise WinError(err)


_EnumChildProc = WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumChildWindows.argtypes = [
    wintypes.HWND,
    _EnumWindowsProc,
    wintypes.LPARAM,
]
_user32.EnumChildWindows.restype = wintypes.BOOL


def EnumChildWindows(parent_hwnd: int, callback: Callable[[int], bool]) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumchildwindows
    """

    def _callback(hwnd: int, _: int) -> int:
        try:
            return 1 if callback(hwnd) else 0
        except Exception:
            return 1

    c_callback = _EnumChildProc(_callback)
    ok = cast(int, _user32.EnumChildWindows(parent_hwnd, c_callback, 0))
    err = get_last_error()
    if ok == 0 and err != 0:
        raise WinError(err)


_user32.SetCursorPos.argtypes = [wintypes.INT, wintypes.INT]
_user32.SetCursorPos.restype = wintypes.BOOL


def SetCursorPos(x: int, y: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setcursorpos
    """
    if _user32.SetCursorPos(x, y) == 0:
        raise WinError(get_last_error())


class _MOUSEINPUT(Structure):
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput
    """

    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", c_ulonglong),
    ]


class _KEYBDINPUT(Structure):
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput
    """

    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", c_ulonglong),
    ]


class _HARDWAREINPUT(Structure):
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-hardwareinput
    """

    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _DUMMYUNIONNAME(Union):
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(Structure):
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input
    """

    _anonymous_ = ("U",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("U", _DUMMYUNIONNAME),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
_user32.SendInput.argtypes = [wintypes.UINT, POINTER(_INPUT), wintypes.INT]
_user32.SendInput.restype = wintypes.UINT


# def SendInput(count: int, inputs: Array[_INPUT], size: int) -> None:
#     usent = cast(int, _user32.SendInput(count, inputs, sizeof(_INPUT)))
#     if usent != count:
#         raise WinError(get_last_error())

SendInput = _user32.SendInput


def ClickMouse(x: int, y: int) -> None:
    SetCursorPos(x, y)

    action_count = 2

    inputs = (_INPUT * action_count)()

    inputs[0].type = INPUT_MOUSE

    inputs[0].U.mi = _MOUSEINPUT()
    inputs[0].U.mi.dx = x
    inputs[0].U.mi.dy = y
    inputs[0].U.mi.dwFlags = MOUSEEVENTF_LEFTDOWN

    inputs[1] = inputs[0]

    inputs[1].U.mi.dwFlags = MOUSEEVENTF_LEFTUP

    usent = cast(int, SendInput(action_count, inputs, sizeof(_INPUT)))
    if usent != action_count:
        raise WinError(get_last_error())


_user32.GetDC.argtypes = [wintypes.HWND]
_user32.GetDC.restype = wintypes.HDC


def GetDC(hwnd: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdc

    HDC GetDC(
        [in] HWND hWnd
    );
    """
    dc = cast(int, _user32.GetDC(hwnd))
    if dc == 0:
        raise WinError(get_last_error())
    return dc


_user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
_user32.ReleaseDC.restype = wintypes.INT


def ReleaseDC(hwnd: int, hdc: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-releasedc

    int ReleaseDC(
        [in] HWND hWnd,
        [in] HDC  hDC
    );
    """
    if cast(int, _user32.ReleaseDC(hwnd, hdc)) == 0:
        raise WinError(get_last_error())


_user32.FrameRect.argtypes = [wintypes.HDC, POINTER(wintypes.RECT), wintypes.HBRUSH]
_user32.FrameRect.restype = wintypes.INT


def FrameRect(hDC: int, rect: wintypes.RECT, hbr: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-framerect

    int FrameRect(
        [in] HDC        hDC,
        [in] const RECT *lprc,
        [in] HBRUSH     hbr
    );
    """
    if cast(int, _user32.FrameRect(hDC, byref(rect), hbr)) == 0:
        raise WinError(get_last_error())
