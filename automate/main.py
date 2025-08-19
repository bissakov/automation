import sys
from pathlib import Path
from typing import Literal, Pattern

project_folder = Path(__file__).resolve().parent.parent
sys.path.append(str(project_folder))

from automate.impl import uia, win32


# FIXME
class Automate:
    def __init__(self, backend: Literal["uia", "win32"]) -> None:
        self.backend: str = backend
        self.ctx: uia.UIAContext | win32.Context
        if backend == "uia":
            self.ctx = uia.UIAContext()
        elif backend == "win32":
            self.ctx = win32.Context()
            raise NotImplementedError()

    @property
    def desktop(self) -> uia.UIAElement:
        return self.ctx.desktop

    def create_condition(
        self,
        pid: int | None = None,
        control_type: uia.ControlType | None = None,
        class_name: str | None = None,
        title: str | Pattern[str] | None = None,
    ) -> uia.Condition:
        condition = self.ctx.create_condition(
            pid=pid,
            control_type=control_type,
            class_name=class_name,
            title=title,
        )
        return condition

    def tree(
        self,
        element: uia.UIAElement,
        max_depth: uia.PositiveInt | None = None,
        draw_outline: bool = False,
        outline_duration: float = 0.005,
    ) -> None:
        return self.ctx.tree(
            element=element,
            max_depth=max_depth,
            draw_outline=draw_outline,
            outline_duration=outline_duration,
        )


def main():
    auto = Automate(backend="uia")

    window = auto.desktop.find_first(
        condition=auto.create_condition(
            control_type=uia.ControlType.Window,
            title="This PC",
            # control_type=uia.ControlType.Window,
            # title="This PC",
        )
    )

    if window:
        window.set_focus()
        print(window.text())
        window.set_focus()
        auto.tree(window, draw_outline=True)


if __name__ == "__main__":
    main()
