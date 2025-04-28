import time
from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Generic, TypeVar, cast

import win32api
import win32con
import win32gui

from automate.common import Color, Point, Rect

E = TypeVar("E", bound="BaseElement")


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
        outline_duration: float = 0.005,
    ) -> None: ...

    @abstractmethod
    def children(self) -> list[E]: ...

    @abstractmethod
    def ichildren(self) -> Generator[E]: ...

    @staticmethod
    def move_cursor(point: Point | tuple[int, int]) -> None:
        if isinstance(point, Point):
            x, y = point.x, point.y
        else:
            x, y = point

        win32api.SetCursorPos((x, y))

    def click_input(self) -> None:
        self.move_cursor(self.rect.mid_point)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def outline(
        self,
        rect: Rect | None = None,
        color: int = Color.GREEN,
        thickness: int = 2,
        delay_after: float = 0.0,
    ) -> None:
        if rect is None:
            rect = self.rect

        dc = win32gui.GetDC(0)

        pen = cast(int, win32gui.CreatePen(win32con.PS_SOLID, thickness, color))
        old_pen = win32gui.SelectObject(dc, pen)
        old_brush = win32gui.SelectObject(
            dc, win32gui.GetStockObject(win32con.NULL_BRUSH)
        )

        win32gui.Rectangle(dc, rect.left, rect.top, rect.right, rect.bottom)

        win32gui.SelectObject(dc, old_brush)
        win32gui.SelectObject(dc, old_pen)

        time.sleep(delay_after)

        win32gui.DeleteObject(pen)
        win32gui.DeleteDC(dc)
