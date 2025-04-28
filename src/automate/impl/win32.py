from __future__ import annotations

import re
import time
from collections.abc import Generator
from functools import cached_property
from typing import Pattern, override

import win32gui

from automate.common import Rect
from automate.errors import Win32NotAWindowError
from automate.impl.base import BaseElement
from automate.win_api import win32_wrapper as win32


class Condition:
    def __init__(
        self,
        pid: int | None = None,
        control_id: int | None = None,
        class_name: str | None = None,
        title: str | Pattern[str] | None = None,
    ) -> None:
        self.pid = pid
        self.control_id = control_id
        self.class_name = class_name
        self.title = title

    def matches(self, element: Window | Element | None) -> bool:
        if not element:
            return False

        result = False
        if self.pid:
            result = self.pid == element.pid
        if self.control_id:
            result = self.control_id == element.control_id
        if self.class_name:
            result = self.class_name == element.class_name
        if self.title:
            if isinstance(self.title, str):
                result = self.title.lower() == element.title.lower()
            else:
                result = re.match(self.title, element.title) is not None
        return result


class TrueCondition(Condition):
    def __init__(self) -> None:
        super().__init__()

    @override
    def matches(self, element: Window | Element | None) -> bool:
        return True


class Element(BaseElement["Element"]):
    def __init__(self, hwnd: int) -> None:
        self.hwnd = hwnd

        self._pid: int | None = None
        self._tid: int | None = None
        self._is_visible: bool
        self._is_enabled: bool
        self._rect: Rect
        self._title: str

    @property
    def is_visible(self) -> bool:
        self._is_visible = win32.IsWindowVisible(self.hwnd)
        return self._is_visible

    @property
    def is_enabled(self) -> bool:
        self._is_enabled = win32.IsWindowEnabled(self.hwnd)
        return self._is_enabled

    @override
    @property
    def rect(self) -> Rect:
        self._rect = Rect(win32.GetWindowRect(self.hwnd))
        return self._rect

    @property
    def title(self) -> str:
        return win32.GetWindowTextW(self.hwnd)

    @cached_property
    def is_window(self) -> bool:
        return win32.IsWindow(self.hwnd)

    @cached_property
    def control_id(self) -> int:
        return win32.GetWindowLongW(self.hwnd, win32.GWL_ID)

    @cached_property
    def class_name(self) -> str:
        return win32.GetClassNameW(self.hwnd)

    @cached_property
    def tid(self) -> int:
        if self._tid:
            return self._tid
        self._tid, self._pid = win32.GetWindowThreadProcessId(self.hwnd)
        return self._tid

    @cached_property
    def pid(self) -> int:
        if self._pid:
            return self._pid
        self._tid, self._pid = win32.GetWindowThreadProcessId(self.hwnd)
        return self._pid

    @cached_property
    def style(self) -> int:
        return win32.GetWindowLongW(self.hwnd, win32.GWL_STYLE)

    @cached_property
    def exstyle(self) -> int:
        return win32.GetWindowLongW(self.hwnd, win32.GWL_EXSTYLE)

    @cached_property
    def owner(self) -> int:
        return win32.GetWindow(self.hwnd, win32.GW_OWNER)

    @cached_property
    def parent(self) -> Element:
        return Element(win32.GetParent(self.hwnd))

    def is_in_current_session(self) -> bool:
        process_sid = win32.ProcessIdToSessionId(win32.GetCurrentProcessId())
        element_sid = win32.ProcessIdToSessionId(self.pid)
        return process_sid == element_sid

    @override
    def children(self) -> list[Element]:
        children = []

        def enum_wnd_proc(hwnd: int, _):
            element = Element(hwnd)
            children.append(element)
            return True

        win32gui.EnumChildWindows(self.hwnd, enum_wnd_proc, 0)
        return children

    @override
    def ichildren(self) -> Generator[Element]:
        # TODO TEMP: investigate how to make win32 callbacks work nicely with generators
        for child in self.children():
            yield child

    def find_first(
        self, condition: Condition, element: Element | None = None
    ) -> Element | None:
        if not element:
            element = self

        for child in element.children():
            if condition.matches(child):
                return child
            if found := self.find_first(condition, child):
                return found
        return None

    def find_all(
        self, condition: Condition, element: Element | None = None
    ) -> list[Element]:
        if not element:
            element = self

        results = []

        for child in element.children():
            if condition.matches(child):
                results.append(child)
            results.extend(child.find_all(element=child, condition=condition))

        return results

    def ifind_all(
        self, condition: Condition, element: Element | None = None
    ) -> Generator[Element]:
        if not element:
            element = self

        for child in element.children():
            if condition.matches(child):
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

        element_repr = (
            "▏   " * depth
            + f"{element_ctrl}{element_idx} - {element.title!r} - "
        )

        try:
            element_repr += f"{element.rect}"
            print(element_repr)
        except Exception:
            element_repr += "(COMError)"
            print(element_repr)
            return

        if draw_outline:
            element.outline(delay_after=outline_duration)

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
            raise Win32NotAWindowError("Current element is not a window...")

    def is_real_window(self) -> bool:
        if not self.is_visible:
            return False

        anc_hwnd = win32.GetAncestor(self.hwnd, win32.GA_ROOTOWNER)
        walk_hwnd = None
        while anc_hwnd != walk_hwnd:
            walk_hwnd = anc_hwnd
            anc_hwnd = win32.GetLastActivePopup(walk_hwnd)
            if win32.IsWindowVisible(anc_hwnd):
                break

        if walk_hwnd != self.hwnd:
            return False

        ti = win32.GetTitleBarInfo(self.hwnd)
        if ti.rgstate[0] & win32.STATE_SYSTEM_INVISIBLE:
            return False

        if self.exstyle & win32.WS_EX_TOOLWINDOW:
            return False

        return True

    def is_focused(self) -> bool:
        return (
            self.hwnd == win32.GetForegroundWindow()
            or self == self.top_window()
        )

    def set_focus(self, delay_after: float = 0.05) -> None:
        if self.is_focused():
            return

        self.show()
        win32.SetWindowPos(
            self.hwnd,
            win32.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32.SWP_NOMOVE | win32.SWP_NOSIZE,
        )
        win32.SetWindowPos(
            self.hwnd,
            win32.HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            win32.SWP_NOMOVE | win32.SWP_NOSIZE,
        )
        time.sleep(delay_after)

    def set_focus2(self) -> None:
        # FIXME: unstable
        if self.is_focused():
            print(f"{self.title!r} is already focused")
            return

        fg_hwnd = win32.GetForegroundWindow()
        fg_tid, _ = win32.GetWindowThreadProcessId(fg_hwnd)

        if not self.is_in_current_session():
            print(f"{self.title!r} is not in current session. Falling back")
            self.set_focus()
            return

        try:
            win32.AttachThreadInput(self.tid, fg_tid, True)
        except Exception as err:
            print(err.args)
            # _, func, msg = err.args
            # print(f"{self.title!r}: {func!r} - {msg!r}. Falling back")
            self.set_focus()
            return

        try:
            if self.is_minimized():
                self.restore()
            elif self.is_maximized():
                self.maximize()
            else:
                self.show()
            win32.SetForegroundWindow(self.hwnd)
        finally:
            win32.AttachThreadInput(self.tid, fg_tid, False)

        # assert self.is_focused(), f"{self.title!r} was not focused"
        print(f"{self.title!r} focused")

    def is_minimized(self) -> bool:
        return win32.IsIconic(self.hwnd)

    def is_maximized(self) -> bool:
        return win32.IsZoomed(self.hwnd)

    def minimize(self) -> None:
        win32.ShowWindow(self.hwnd, win32.SW_MINIMIZE)

    def maximize(self) -> None:
        win32.ShowWindow(self.hwnd, win32.SW_MAXIMIZE)

    def restore(self) -> None:
        win32.ShowWindow(self.hwnd, win32.SW_RESTORE)

    def show(self) -> None:
        win32.ShowWindow(self.hwnd, win32.SW_SHOW)

    def top_window(self) -> Window | None:
        window = None

        def enum_wnd_proc(hwnd: int, _) -> bool:
            nonlocal window
            win = Window(hwnd)
            if win.is_visible and win.title:
                window = win
                return False
            return True

        win32gui.EnumWindows(enum_wnd_proc, 0)

        return window

    @override
    def __eq__(self, window: object, /) -> bool:
        if not isinstance(window, Window):
            raise NotImplementedError
        return self.hwnd == window.hwnd


class Win32Context:
    def __init__(self) -> None:
        pass

    def create_condition(
        self,
        pid: int | None = None,
        control_id: int | None = None,
        class_name: str | None = None,
        title: str | Pattern[str] | None = None,
    ) -> Condition:
        if not pid and not control_id and not class_name and not title:
            raise ValueError("Every argument is None...")

        condition = Condition(
            pid=pid, control_id=control_id, class_name=class_name, title=title
        )

        return condition

    def find_window(self, condition: Condition) -> Window | None:
        return next(
            (window for window in self.windows() if condition.matches(window)),
            None,
        )

    @classmethod
    def windows(cls) -> list[Window]:
        _windows = []

        def enum_wnd_proc(hwnd: int, _):
            if (window := Window(hwnd)).is_real_window():
                _windows.append(window)
                return True

        win32gui.EnumWindows(enum_wnd_proc, 0)

        return _windows

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
    ctx = Win32Context()
    # # ctx.tree()
    #
    windows = ctx.windows()
    print(len(windows))
    for win in windows:
        print(win.is_in_current_session())
        # print(f"{win.title!r}, {win.class_name!r}, {(win.exstyle)}")
    #     # win.fallback_focus()
    #     # print(f"{win.title!r} - {win.is_focused()}")
    #     # time.sleep(0.5)


if __name__ == "__main__":
    main()
