from __future__ import annotations

import random
from ctypes.wintypes import RECT
from functools import cached_property
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Iterator


class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y

    def __iter__(self) -> Iterator[int]:
        return iter((self.x, self.y))

    @override
    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"


class Rect:
    def __init__(self, native_rect: RECT | tuple[int, int, int, int]) -> None:
        if isinstance(native_rect, tuple):
            self._rect: RECT = RECT()
            (
                self._rect.left,
                self._rect.top,
                self._rect.right,
                self._rect.bottom,
            ) = native_rect
        else:
            self._rect = native_rect

        self.left: int = self._rect.left
        self.top: int = self._rect.top
        self.right: int = self._rect.right
        self.bottom: int = self._rect.bottom

    @cached_property
    def width(self) -> int:
        return self.right - self.left

    @cached_property
    def height(self) -> int:
        return self.bottom - self.top

    @cached_property
    def center(self) -> Point:
        return Point(
            x=self.left + int(float(self.width) / 2.0),
            y=self.top + int(float(self.height) / 2.0),
        )

    def has_area(self) -> bool:
        return (self.right - self.left) != 0 and (self.bottom - self.top) != 0

    def random_point(self) -> Point:
        return Point(
            x=random.randint(self.left, self.right),
            y=random.randint(self.top, self.bottom),
        )

    @override
    def __repr__(self) -> str:
        return f"Rect(l={self.left}, t={self.top}, r={self.right}, b={self.bottom})"


class Color:
    RED: int = 0x0000FF
    GREEN: int = 0x00FF00
    BLUE: int = 0xFF0000

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> int:
        return r | (g << 8) | (b << 16)
