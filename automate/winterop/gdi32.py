from __future__ import annotations

from ctypes import WinDLL, WinError, get_last_error, wintypes
from typing import cast

_gdi32 = WinDLL("gdi32", use_last_error=True)


_gdi32.CreatePen.argtypes = [wintypes.INT, wintypes.INT, wintypes.COLORREF]
_gdi32.CreatePen.restype = wintypes.HPEN


def CreatePen(iStyle: int, cWidth: int, color: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createpen

    HPEN CreatePen(
        [in] int      iStyle,
        [in] int      cWidth,
        [in] COLORREF color
    );
    """
    pen = cast(int, _gdi32.CreatePen(iStyle, cWidth, color))
    if pen == 0:
        raise WinError(get_last_error())
    return pen


_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ


def SelectObject(hdc: int, h: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-selectobject

    HGDIOBJ SelectObject(
        [in] HDC     hdc,
        [in] HGDIOBJ h
    );
    """
    obj = cast(int, _gdi32.SelectObject(hdc, h))
    if obj == 0:
        raise WinError(get_last_error())
    return obj


_gdi32.GetStockObject.argtypes = [wintypes.INT]
_gdi32.GetStockObject.restype = wintypes.HGDIOBJ


def GetStockObject(i: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getstockobject

    HGDIOBJ GetStockObject(
        [in] int i
    );
    """
    obj = cast(int, _gdi32.GetStockObject(i))
    if obj == 0:
        raise WinError(get_last_error())
    return obj


_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteObject.restype = wintypes.BOOL


def DeleteObject(ho: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-deleteobject

    BOOL DeleteObject(
        [in] HGDIOBJ ho
    );
    """
    ok = cast(int, _gdi32.DeleteObject(ho))
    err = get_last_error()
    if ok == 0 and err != 0:
        raise WinError(err)


_gdi32.Rectangle.argtypes = [wintypes.HDC, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT]
_gdi32.Rectangle.restype = wintypes.BOOL


def Rectangle(hdc: int, left: int, top: int, right: int, bottom: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-rectangle

    BOOL Rectangle(
        [in] HDC hdc,
        [in] int left,
        [in] int top,
        [in] int right,
        [in] int bottom
    );
    """
    ok = cast(int, _gdi32.Rectangle(hdc, left, top, right, bottom))
    if ok == 0:
        raise WinError(get_last_error())


_gdi32.DeleteDC.argtypes = [wintypes.HDC]
_gdi32.DeleteDC.restype = wintypes.BOOL


def DeleteDC(hdc: int) -> None:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-deletedc

    BOOL DeleteDC(
        [in] HDC hdc
    );
    """
    ok = cast(int, _gdi32.DeleteDC(hdc))
    if ok == 0:
        raise WinError(get_last_error())


_gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
_gdi32.CreateSolidBrush.restype = wintypes.HBRUSH


def CreateSolidBrush(color: int) -> int:
    """
    https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-createsolidbrush

    HBRUSH CreateSolidBrush(
        [in] COLORREF color
    );
    """
    brush = cast(int, _gdi32.CreateSolidBrush(color))
    if brush == 0:
        raise WinError(get_last_error())
    return brush
