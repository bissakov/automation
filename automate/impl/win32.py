from __future__ import annotations

import re
import time
from functools import cached_property
from typing import TYPE_CHECKING, NamedTuple

from typing_extensions import cast, override

from automate.common import Rect
from automate.impl.base import BaseElement
from automate.winterop import kernel32, user32
from automate.winterop import win32_constants as win32_con

if TYPE_CHECKING:
    from collections.abc import Generator
    from re import Pattern
    from types import TracebackType


class Condition(NamedTuple):
    pid: int | None = None
    control_id: int | None = None
    class_name: str | None = None
    title: str | Pattern[str] | None = None


def windows() -> list[Window]:
    _windows: list[Window] = []

    def callback(hwnd: int) -> bool:
        if (window := Window(hwnd)).is_real_window():
            _windows.append(window)
            return True
        return True

    user32.EnumWindows(callback)

    return _windows


def top_window() -> Window | None:
    return windows()[0]


class Element(BaseElement["Element"]):
    def __init__(self, hwnd: int) -> None:
        super().__init__()
        self.hwnd: int = hwnd

        self._pid: int | None = None
        self._tid: int | None = None
        self._is_visible: bool
        self._is_enabled: bool
        self._rect: Rect
        self._title: str

    @property
    def is_visible(self) -> bool:
        self._is_visible = user32.IsWindowVisible(self.hwnd)
        return self._is_visible

    @property
    def is_enabled(self) -> bool:
        self._is_enabled = user32.IsWindowEnabled(self.hwnd)
        return self._is_enabled

    @property
    @override
    def rect(self) -> Rect:
        self._rect = Rect(user32.GetWindowRect(self.hwnd))
        return self._rect

    @property
    def title(self) -> str:
        return user32.GetWindowTextW(self.hwnd)

    @cached_property
    def is_window(self) -> bool:
        return user32.IsWindow(self.hwnd)

    @cached_property
    def control_id(self) -> int:
        return user32.GetWindowLongW(self.hwnd, win32_con.GWL_ID)

    @cached_property
    def class_name(self) -> str:
        return user32.GetClassNameW(self.hwnd)

    @cached_property
    def tid(self) -> int:
        if self._tid:
            return self._tid
        self._tid, self._pid = user32.GetWindowThreadProcessId(self.hwnd)
        return self._tid

    @cached_property
    def pid(self) -> int:
        if self._pid:
            return self._pid
        self._tid, self._pid = user32.GetWindowThreadProcessId(self.hwnd)
        return self._pid

    @cached_property
    def style(self) -> int:
        return user32.GetWindowLongW(self.hwnd, win32_con.GWL_STYLE)

    @cached_property
    def exstyle(self) -> int:
        return user32.GetWindowLongW(self.hwnd, win32_con.GWL_EXSTYLE)

    @cached_property
    def owner(self) -> int:
        return user32.GetWindow(self.hwnd, win32_con.GW_OWNER)

    @cached_property
    def parent(self) -> Element:
        return Element(user32.GetParent(self.hwnd))

    def is_in_current_session(self) -> bool:
        process_sid = kernel32.ProcessIdToSessionId(kernel32.GetCurrentProcessId())
        element_sid = kernel32.ProcessIdToSessionId(self.pid)
        return process_sid == element_sid

    @override
    def children(self) -> list[Element]:
        children: list[Element] = []

        def enum_wnd_proc(hwnd: int) -> bool:
            element = Element(hwnd)
            children.append(element)
            return True

        user32.EnumChildWindows(self.hwnd, enum_wnd_proc)
        return children

    @override
    def ichildren(self) -> Generator[Element]:
        # TODO TEMP: investigate how to make user32 callbacks work nicely with generators
        for child in self.children():
            yield child

    def satisfies(self, condition: Condition) -> bool:
        result = False
        if condition.pid:
            result = condition.pid == self.pid
        if condition.control_id:
            result = condition.control_id == self.control_id
        if condition.class_name:
            result = condition.class_name == self.class_name
        if condition.title:
            if isinstance(condition.title, str):
                title = condition.title
                result = title.lower() == self.title.lower()
            else:
                title = condition.title
                result = re.match(title, self.title) is not None
        return result

    def find_first(
        self,
        condition: Condition,
        element: Element | None = None,
    ) -> Element | None:
        if not element:
            element = self

        for child in element.children():
            if child.satisfies(condition):
                return child
            if found := self.find_first(element=child, condition=condition):
                return found
        return None

    def find_all(
        self,
        condition: Condition,
        element: Element | None = None,
    ) -> list[Element]:
        return list(self.ifind_all(element=element, condition=condition))

    def ifind_all(
        self,
        condition: Condition,
        element: Element | None = None,
    ) -> Generator[Element]:
        if not element:
            element = self

        for child in element.children():
            if child.satisfies(condition=condition):
                yield child
            yield from child.ifind_all(element=child, condition=condition)

    @override
    def tree(
        self,
        element: Element | None = None,
        max_depth: int | None = None,
        counters: dict[str, int] | None = None,
        depth: int = 0,
        draw_outline: bool = False,
        outline_duration: float = 0.005,
    ) -> None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be a non-negative integer or None")

        if counters is None:
            counters = {}

        if not element:
            element = self

        element_ctrl = element.class_name
        counters[element_ctrl] = counters.get(element_ctrl, 0) + 1
        element_idx = counters[element_ctrl] - 1

        element_repr = "▏   " * depth + f"{element_ctrl}{element_idx} - {element.title!r} - "

        try:
            element_repr += f"{element.rect}"
            print(element_repr)
        except Exception:
            element_repr += "(COMError)"
            print(element_repr)
            return

        if draw_outline:
            element.outline(duration_ms=outline_duration)

        if max_depth is None or depth < max_depth:
            for child in element.children():
                self.tree(
                    element=child,
                    max_depth=max_depth,
                    counters=counters,
                    depth=depth + 1,
                    draw_outline=draw_outline,
                    outline_duration=outline_duration,
                )

    @override
    def __repr__(self) -> str:
        return (
            f"Element(title={self.title!r}, "
            f"control_id={self.control_id!r}, "
            f"class_name={self.class_name!r}, "
            f"pid={self.pid}, "
            f"rect={self.rect})"
        )


class Window(Element):
    def __init__(self, hwnd: int) -> None:
        super().__init__(hwnd)
        if not self.is_window:
            raise Exception("Current element is not a window...")

    def is_real_window(self) -> bool:
        if not self.is_visible:
            return False

        anc_hwnd = user32.GetAncestor(self.hwnd, win32_con.GA_ROOTOWNER)
        walk_hwnd = None
        while anc_hwnd != walk_hwnd:
            walk_hwnd = anc_hwnd
            anc_hwnd = user32.GetLastActivePopup(walk_hwnd)
            if user32.IsWindowVisible(anc_hwnd):
                break

        if walk_hwnd != self.hwnd:
            return False

        ti = user32.get_title_bar_info(self.hwnd)
        if cast(list[int], ti.rgstate)[0] & win32_con.STATE_SYSTEM_INVISIBLE:
            return False

        if self.exstyle & win32_con.WS_EX_TOOLWINDOW:
            return False

        return True

    def is_focused(self) -> bool:
        print(self.hwnd == user32.GetForegroundWindow())
        print(top_window())
        print(self == top_window())
        return self.hwnd == user32.GetForegroundWindow() or self == self.top_window()

    def focus(self, delay_after: float = 0.05) -> None:
        # if self.is_focused():
        #     return

        self.show()
        user32.SetWindowPos(
            self.hwnd,
            win32_con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32_con.SWP_NOMOVE | win32_con.SWP_NOSIZE,
        )
        user32.SetWindowPos(
            self.hwnd,
            win32_con.HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            win32_con.SWP_NOMOVE | win32_con.SWP_NOSIZE,
        )
        time.sleep(delay_after)

    def _focus(self) -> None:
        # FIXME: unstable
        if self.is_focused():
            print(f"{self.title!r} is already focused")
            return

        fg_hwnd = user32.GetForegroundWindow()
        fg_tid, _ = user32.GetWindowThreadProcessId(fg_hwnd)

        if not self.is_in_current_session():
            print(f"{self.title!r} is not in current session. Falling back")
            self.focus()
            return

        try:
            user32.AttachThreadInput(self.tid, fg_tid, True)
        except Exception as err:
            print(err.args)
            # _, func, msg = err.args
            # print(f"{self.title!r}: {func!r} - {msg!r}. Falling back")
            self.focus()
            return

        try:
            if self.is_minimized():
                self.restore()
            elif self.is_maximized():
                self.maximize()
            else:
                self.show()
            user32.SetForegroundWindow(self.hwnd)
        finally:
            user32.AttachThreadInput(self.tid, fg_tid, False)

        # assert self.is_focused(), f"{self.title!r} was not focused"
        print(f"{self.title!r} focused")

    def is_minimized(self) -> bool:
        return user32.IsIconic(self.hwnd)

    def is_maximized(self) -> bool:
        return user32.IsZoomed(self.hwnd)

    def minimize(self) -> None:
        user32.ShowWindow(self.hwnd, win32_con.SW_MINIMIZE)

    def maximize(self) -> None:
        user32.ShowWindow(self.hwnd, win32_con.SW_MAXIMIZE)

    def restore(self) -> None:
        user32.ShowWindow(self.hwnd, win32_con.SW_RESTORE)

    def show(self) -> None:
        user32.ShowWindow(self.hwnd, win32_con.SW_SHOW)

    def top_window(self) -> Window | None:
        window = None

        def callback(hwnd: int) -> bool:
            nonlocal window
            if window:
                return False

            win = Window(hwnd)
            if win.is_visible and win.title:
                window = win
                return False
            return True

        user32.EnumWindows(callback)

        return window

    @override
    def __eq__(self, window: object, /) -> bool:
        if not isinstance(window, Window):
            raise NotImplementedError
        return self.hwnd == window.hwnd


class Context:
    def __init__(self) -> None:
        pass

    def open(self) -> Context:
        return self

    def exit(self) -> None: ...

    def __enter__(self) -> Context:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def find_window(self, condition: Condition) -> Window | None:
        return next((w for w in self.windows() if w.satisfies(condition)), None)

    @classmethod
    def windows(cls) -> list[Window]:
        _windows: list[Window] = []

        def callback(hwnd: int) -> bool:
            if (window := Window(hwnd)).is_real_window():
                _windows.append(window)
                return True
            return True

        user32.EnumWindows(callback)

        return _windows

    def top_window(self) -> Window | None:
        return self.windows()[0]

    @classmethod
    def tree(
        cls,
        element: Element | None = None,
        max_depth: int | None = None,
        draw_outline: bool = False,
        outline_duration: float = 0.005,
    ) -> None:
        if not element:
            for window in cls.windows():
                window.tree(
                    max_depth=max_depth,
                    draw_outline=draw_outline,
                    outline_duration=outline_duration,
                )
        else:
            element.tree(
                max_depth=max_depth,
                draw_outline=draw_outline,
                outline_duration=outline_duration,
            )


def main() -> None:
    with Context() as ctx:
        win = ctx.find_window(Condition(title="This PC"))
        if win:
            win.focus(1)
            print(win.title, win.is_focused())

        # for win in ctx.windows():
        #     win.focus(0.5)
        #     print(win.title, win.is_focused())

        # win = ctx.find_window(Condition(title="This PC"))
        # print("win: ", win)


if __name__ == "__main__":
    main()
