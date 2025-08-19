from __future__ import annotations

from abc import ABC, abstractmethod
from ctypes import WinError, get_last_error, sizeof
from time import sleep
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from automate.common import Color
from automate.winterop import user32
from automate.winterop import win32_constants as win32con
from automate.winterop import winterop

if TYPE_CHECKING:
    from collections.abc import Generator

    from automate.common import Point, Rect

E = TypeVar("E")


class BaseElement(ABC, Generic[E]):
    def __init__(self) -> None:
        super().__init__()
        self._rect: Rect

    @property
    @abstractmethod
    def rect(self) -> Rect: ...

    @abstractmethod
    def tree(
        self,
        element: E | None = None,
        max_depth: int | None = None,
        counters: dict[str, int] | None = None,
        depth: int = 0,
        draw_outline: bool = False,
        outline_duration_ms: int = 10,
    ) -> None: ...

    @abstractmethod
    def children(self) -> list[E]: ...

    @abstractmethod
    def ichildren(self) -> Generator[E]: ...

    @staticmethod
    def move_cursor(point: Point | tuple[int, int]) -> None:
        x, y = point
        user32.SetCursorPos(x, y)

    def click_mouse(self) -> bool:
        return winterop.click_mouse(*self.rect.center)

    def type_text(self, text: str, delay_ms: int = 0) -> bool:
        if not text:
            return True
        return winterop.type_text(text=text, delay_ms=delay_ms)

    def outline(
        self,
        rect: Rect | None = None,
        color: int = Color.GREEN,
        thickness: int = 2,
        duration_ms: int = 0,
    ) -> None:
        if rect is None:
            rect = self.rect

        if not rect.has_area():
            return

        winterop.outline(
            left=rect.left,
            top=rect.top,
            right=rect.right,
            bottom=rect.bottom,
            thickness=thickness,
            color=color,
            duration_ms=duration_ms,
        )
