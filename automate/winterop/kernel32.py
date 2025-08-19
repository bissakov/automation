from __future__ import annotations

from ctypes import POINTER, WinDLL, WinError, byref, get_last_error, wintypes
from typing import cast

_kernel32 = WinDLL("kernel32", use_last_error=True)


_kernel32.GetCurrentProcessId.argtypes = []
_kernel32.GetCurrentProcessId.restype = wintypes.DWORD


def GetCurrentProcessId() -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentprocessid

    DWORD GetCurrentProcessId();
    """
    return cast(int, _kernel32.GetCurrentProcessId())


_kernel32.ProcessIdToSessionId.argtypes = [
    wintypes.DWORD,
    POINTER(wintypes.DWORD),
]
_kernel32.ProcessIdToSessionId.restype = wintypes.BOOL


def ProcessIdToSessionId(dwProcessId: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-processidtosessionid

    BOOL ProcessIdToSessionId(
        [in]  DWORD dwProcessId,
        [out] DWORD *pSessionId
    );
    """
    session_id = wintypes.DWORD()
    if _kernel32.ProcessIdToSessionId(dwProcessId, byref(session_id)) == 0:
        raise WinError(get_last_error())
    return session_id.value
