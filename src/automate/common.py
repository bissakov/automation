from ctypes.wintypes import RECT
from typing import override


class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y

    @override
    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"


class Rect:
    def __init__(self, native_rect: RECT | tuple[int, int, int, int]) -> None:
        if isinstance(native_rect, tuple):
            self._rect = RECT()
            (
                self._rect.left,
                self._rect.top,
                self._rect.right,
                self._rect.bottom,
            ) = native_rect
        else:
            self._rect = native_rect

        self.left = self._rect.left
        self.top = self._rect.top
        self.right = self._rect.right
        self.bottom = self._rect.bottom

        self._width: int
        self._height: int
        self._mid_point: Point

    @property
    def width(self) -> int:
        self._width = self.right - self.left
        return self._width

    @property
    def height(self) -> int:
        self._height = self.bottom - self.top
        return self._height

    @property
    def mid_point(self) -> Point:
        self._mid_point.x = self.left + int(float(self.width) / 2.0)
        self._mid_point.y = self.top + int(float(self.height) / 2.0)
        return self._mid_point

    def has_area(self) -> bool:
        return (self.right - self.left) != 0 and (self.bottom - self.top) != 0

    def __repr__(self) -> str:
        return f"Rect(l={self.left}, t={self.top}, r={self.right}, b={self.bottom})"


class Color:
    RED: int = 0x0000FF
    GREEN: int = 0x00FF00
    BLUE: int = 0xFF0000

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> int:
        if not ((0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255)):
            raise ValueError(f"Out of bounds - {r=!r}, {g=!r}, {b=!r}")
        return r | (g << 8) | (b << 16)
