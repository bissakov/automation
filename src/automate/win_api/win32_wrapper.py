import ctypes
from ctypes import WinDLL, create_unicode_buffer, wintypes

MAX_CHARS = 256
CCHILDREN_TITLEBAR = 5

GA_PARENT = 1
GA_ROOT = 2
GA_ROOTOWNER = 3

GW_CHILD = 5
GW_ENABLEDPOPUP = 6
GW_HWNDFIRST = 0
GW_HWNDLAST = 1
GW_HWNDNEXT = 2
GW_HWNDPREV = 3
GW_OWNER = 4

GWL_EXSTYLE = -20
GWL_HINSTANCE = -6
GWL_HWNDPARENT = -8
GWL_ID = -12
GWL_STYLE = -16
GWL_USERDATA = -21
GWL_WNDPROC = -4

HWND_BOTTOM = 1
HWND_NOTOPMOST = -2
HWND_TOP = 0
HWND_TOPMOST = -1

SWP_ASYNCWINDOWPOS = 0x4000
SWP_DEFERERASE = 0x2000
SWP_DRAWFRAME = 0x0020
SWP_FRAMECHANGED = 0x0020
SWP_HIDEWINDOW = 0x0080
SWP_NOACTIVATE = 0x0010
SWP_NOCOPYBITS = 0x0100
SWP_NOMOVE = 0x0002
SWP_NOOWNERZORDER = 0x0200
SWP_NOREDRAW = 0x0008
SWP_NOREPOSITION = 0x0200
SWP_NOSENDCHANGING = 0x0400
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040

SW_HIDE = 0
SW_NORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9
SW_SHOWDEFAULT = 10
SW_FORCEMINIMIZE = 11

WS_EX_DLGMODALFRAME = 1
WS_EX_NOPARENTNOTIFY = 4
WS_EX_TOPMOST = 8
WS_EX_ACCEPTFILES = 16
WS_EX_TRANSPARENT = 32
WS_EX_MDICHILD = 64
WS_EX_TOOLWINDOW = 128
WS_EX_WINDOWEDGE = 256
WS_EX_CLIENTEDGE = 512
WS_EX_CONTEXTHELP = 1024
WS_EX_RIGHT = 4096
WS_EX_LEFT = 0
WS_EX_RTLREADING = 8192
WS_EX_LTRREADING = 0
WS_EX_LEFTSCROLLBAR = 16384
WS_EX_RIGHTSCROLLBAR = 0
WS_EX_CONTROLPARENT = 65536
WS_EX_STATICEDGE = 131072
WS_EX_APPWINDOW = 262144
WS_EX_OVERLAPPEDWINDOW = WS_EX_WINDOWEDGE | WS_EX_CLIENTEDGE
WS_EX_PALETTEWINDOW = WS_EX_WINDOWEDGE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
WS_EX_LAYERED = 0x00080000
WS_EX_NOINHERITLAYOUT = 0x00100000
WS_EX_LAYOUTRTL = 0x00400000
WS_EX_COMPOSITED = 0x02000000
WS_EX_NOACTIVATE = 0x08000000

STATE_SYSTEM_UNAVAILABLE = 1
STATE_SYSTEM_SELECTED = 2
STATE_SYSTEM_FOCUSED = 4
STATE_SYSTEM_PRESSED = 8
STATE_SYSTEM_CHECKED = 16
STATE_SYSTEM_MIXED = 32
STATE_SYSTEM_READONLY = 64
STATE_SYSTEM_HOTTRACKED = 128
STATE_SYSTEM_DEFAULT = 256
STATE_SYSTEM_EXPANDED = 512
STATE_SYSTEM_COLLAPSED = 1024
STATE_SYSTEM_BUSY = 2048
STATE_SYSTEM_FLOATING = 4096
STATE_SYSTEM_MARQUEED = 8192
STATE_SYSTEM_ANIMATED = 16384
STATE_SYSTEM_INVISIBLE = 32768
STATE_SYSTEM_OFFSCREEN = 65536
STATE_SYSTEM_SIZEABLE = 131072
STATE_SYSTEM_MOVEABLE = 262144
STATE_SYSTEM_SELFVOICING = 524288
STATE_SYSTEM_FOCUSABLE = 1048576
STATE_SYSTEM_SELECTABLE = 2097152
STATE_SYSTEM_LINKED = 4194304
STATE_SYSTEM_TRAVERSED = 8388608
STATE_SYSTEM_MULTISELECTABLE = 16777216
STATE_SYSTEM_EXTSELECTABLE = 33554432
STATE_SYSTEM_ALERT_LOW = 67108864
STATE_SYSTEM_ALERT_MEDIUM = 134217728
STATE_SYSTEM_ALERT_HIGH = 268435456
STATE_SYSTEM_VALID = 536870911


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-titlebarinfo
class TITLEBARINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcTitleBar", wintypes.RECT),
        ("rgstate", wintypes.DWORD * (CCHILDREN_TITLEBAR + 1)),
    ]


_user32 = WinDLL("user32", use_last_error=True)
_kernel32 = WinDLL("kernel32", use_last_error=True)


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getlastactivepopup
_user32.GetLastActivePopup.argtypes = [wintypes.HWND]
_user32.GetLastActivePopup.restype = wintypes.HWND


def GetLastActivePopup(hWnd: int) -> int:
    return _user32.GetLastActivePopup(hWnd)


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-gettitlebarinfo
_user32.GetTitleBarInfo.argtypes = [wintypes.HWND, ctypes.POINTER(TITLEBARINFO)]
_user32.GetTitleBarInfo.restype = wintypes.BOOL


def GetTitleBarInfo(hWnd: int) -> TITLEBARINFO:
    ti = TITLEBARINFO()
    ti.cbSize = ctypes.sizeof(ti)
    if not _user32.GetTitleBarInfo(hWnd, ctypes.byref(ti)):
        raise ctypes.WinError(ctypes.get_last_error())
    return ti


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindow
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL


def IsWindow(hWnd: int) -> bool:
    return bool(_user32.IsWindow(hWnd))


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclassnamew
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_user32.GetClassNameW.restype = wintypes.INT


def GetClassNameW(hWnd: int) -> str:
    buffer = create_unicode_buffer(MAX_CHARS)
    name_length = _user32.GetClassNameW(hWnd, buffer, MAX_CHARS)
    if name_length <= 0:
        return ""
    return buffer.value


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, wintypes.LPDWORD]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def GetWindowThreadProcessId(hWnd: int) -> tuple[int, int]:
    pid = wintypes.DWORD()
    tid = _user32.GetWindowThreadProcessId(hWnd, ctypes.byref(pid))
    if tid == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    return tid, pid.value


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowrect
_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL


def GetWindowRect(hWnd: int) -> wintypes.RECT:
    rect = wintypes.RECT()
    if _user32.GetWindowRect(hWnd, ctypes.byref(rect)) == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    return rect


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow
_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND


def GetForegroundWindow() -> int:
    hWnd = _user32.GetForegroundWindow()
    if not hWnd:
        raise ValueError(
            "The result of 'GetForegroundWindow' is None. "
            "The foreground window can be NULL in certain circumstances, "
            "such as when a window is losing activation."
        )
    return hWnd


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindowvisible
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL


def IsWindowVisible(hWnd: int) -> bool:
    return _user32.IsWindowVisible(hWnd) != 0


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindowenabled
_user32.IsWindowEnabled.argtypes = [wintypes.HWND]
_user32.IsWindowEnabled.restype = wintypes.BOOL


def IsWindowEnabled(hWnd: int) -> bool:
    return _user32.IsWindowEnabled(hWnd) != 0


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowtextw
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
_user32.GetWindowTextW.restype = wintypes.INT


def GetWindowTextW(hWnd: int) -> str:
    buffer = create_unicode_buffer(MAX_CHARS)
    name_length = _user32.GetWindowTextW(hWnd, buffer, MAX_CHARS)
    if name_length <= 0:
        return ""
    return buffer.value


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getparent
_user32.GetParent.argtypes = [wintypes.HWND]
_user32.GetParent.restype = wintypes.HWND


def GetParent(hWnd: int) -> int:
    return _user32.GetParent(hWnd)


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput
_user32.AttachThreadInput.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.BOOL,
]
_user32.AttachThreadInput.restype = wintypes.BOOL


def AttachThreadInput(idAttach: int, idAttachTo: int, fAttach: bool) -> None:
    if _user32.AttachThreadInput(idAttach, idAttachTo, fAttach) == 0:
        raise ctypes.WinError(ctypes.get_last_error())


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowlongw
_user32.GetWindowLongW.argtypes = [wintypes.HWND, wintypes.INT]
_user32.GetWindowLongW.restype = wintypes.LONG


def GetWindowLongW(hWnd: int, nIndex: int) -> int:
    res = _user32.GetWindowLongW(hWnd, nIndex)
    err = ctypes.get_last_error()
    if res == 0 and err != 0:
        raise ctypes.WinError(err)
    return res


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindow
_user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetWindow.restype = wintypes.HWND


def GetWindow(hWnd: int, uCmd: int) -> int:
    res_hWnd = _user32.GetWindow(hWnd, uCmd)
    if res_hWnd is None:
        raise ctypes.WinError(ctypes.get_last_error())
    return res_hWnd


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getancestor
_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetAncestor.restype = wintypes.HWND


def GetAncestor(hWnd: int, gaFlags: int) -> int:
    anc_hWnd = _user32.GetAncestor(hWnd, gaFlags)
    if anc_hWnd is None:
        raise ctypes.WinError(ctypes.get_last_error())
    return anc_hWnd


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-isiconic
_user32.IsIconic.argtypes = [wintypes.HWND]
_user32.IsIconic.restype = wintypes.BOOL


def IsIconic(hWnd: int) -> bool:
    return bool(_user32.IsIconic(hWnd))


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iszoomed
_user32.IsZoomed.argtypes = [wintypes.HWND]
_user32.IsZoomed.restype = wintypes.BOOL


def IsZoomed(hWnd: int) -> bool:
    return bool(_user32.IsZoomed(hWnd))


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
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
    hWnd: int,
    hWndInsertAfter: int,
    X: int,
    Y: int,
    cx: int,
    cy: int,
    uFlags: int,
) -> None:
    res = _user32.SetWindowPos(hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags)
    if res == 0:
        raise ctypes.WinError(ctypes.get_last_error())


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL


def SetForegroundWindow(hWnd: int) -> None:
    res = _user32.SetForegroundWindow(hWnd)
    if res == 0:
        raise ctypes.WinError(ctypes.get_last_error())


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
_user32.ShowWindow.argtypes = [wintypes.HWND, wintypes.INT]
_user32.ShowWindow.restype = wintypes.BOOL


def ShowWindow(hWnd: int, nCmdShow: int) -> None:
    _user32.ShowWindow(hWnd, nCmdShow)


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows
# FIXME
_user32.EnumWindows.argtypes = [
    wintypes.WPARAM,
]
_user32.EnumWindows.restype = wintypes.BOOL


# https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocessid
_kernel32.GetCurrentProcessId.argtypes = []
_kernel32.GetCurrentProcessId.restype = wintypes.DWORD


def GetCurrentProcessId() -> int:
    return _kernel32.GetCurrentProcessId()


# https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-processidtosessionid
_kernel32.ProcessIdToSessionId.argtypes = [
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
_kernel32.ProcessIdToSessionId.restype = wintypes.BOOL


def ProcessIdToSessionId(dwProcessId: int) -> int:
    session_id = wintypes.DWORD()
    res = _kernel32.ProcessIdToSessionId(dwProcessId, ctypes.byref(session_id))
    if res == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return session_id.value
