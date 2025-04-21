import time
from ctypes.wintypes import RECT
from enum import Enum
from typing import Generator, Iterable, Optional, Union, cast

import comtypes
import comtypes.client
import win32con
import win32gui
from comtypes.gen.UIAutomationClient import (
    CUIAutomation,
    IUIAutomation,
    IUIAutomationCondition,
    IUIAutomationElement,
    IUIAutomationElementArray,
    PropertyConditionFlags_IgnoreCase,
)

uia_dll = comtypes.client.GetModule("UIAutomationCore.dll")


class Property(int, Enum):
    ProcessId = uia_dll.UIA_ProcessIdPropertyId
    ControlType = uia_dll.UIA_ControlTypePropertyId
    ClassName = uia_dll.UIA_ClassNamePropertyId
    Title = uia_dll.UIA_NamePropertyId


class Scope(int, Enum):
    Ancestors = uia_dll.TreeScope_Ancestors
    Children = uia_dll.TreeScope_Children
    Descendants = uia_dll.TreeScope_Descendants
    Element = uia_dll.TreeScope_Element
    Parent = uia_dll.TreeScope_Parent
    Subtree = uia_dll.TreeScope_Subtree


class ControlType(int, Enum):
    AppBar = 50040
    Button = 50000
    Calendar = 50001
    CheckBox = 50002
    ComboBox = 50003
    Custom = 50025
    DataGrid = 50028
    DataItem = 50029
    Document = 50030
    Edit = 50004
    Group = 50026
    Header = 50034
    HeaderItem = 50035
    Hyperlink = 50005
    Image = 50006
    List = 50008
    ListItem = 50007
    MenuBar = 50010
    Menu = 50009
    MenuItem = 50011
    Pane = 50033
    ProgressBar = 50012
    RadioButton = 50013
    ScrollBar = 50014
    SemanticZoom = 50039
    Separator = 50038
    Slider = 50015
    Spinner = 50016
    SplitButton = 50031
    StatusBar = 50017
    Tab = 50018
    TabItem = 50019
    Table = 50036
    Text = 50020
    Thumb = 50027
    TitleBar = 50037
    ToolBar = 50021
    ToolTip = 50022
    Tree = 50023
    TreeItem = 50024
    Window = 50032


class Color:
    RED = 0x0000FF
    GREEN = 0x00FF00
    BLUE = 0xFF0000

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> int:
        if not ((0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255)):
            raise ValueError(f"Out of bounds - {r=!r}, {g=!r}, {b=!r}")
        return r | (g << 8) | (b << 16)


class ElementNotFoundError(Exception): ...


class ElementNotFocusedError(Exception): ...


class ConditionNotCreatedError(Exception): ...


class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"


class Rect:
    def __init__(self, _rect: RECT) -> None:
        self._rect = _rect
        self.left = _rect.left
        self.top = _rect.top
        self.right = _rect.right
        self.bottom = _rect.bottom

        self.width = self.right - self.left
        self.height = self.bottom - self.top

        self.mid_point = Point(
            x=(self.left + int(float(self.width) / 2.0)),
            y=(self.top + int(float(self.height) / 2.0)),
        )

    def __repr__(self) -> str:
        return f"Rect(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"


class UIAElement:
    def __init__(self, uia: IUIAutomationElement) -> None:
        self.uia = uia
        self.title: str = self.uia.CurrentName
        self.control_type: ControlType = ControlType(
            self.uia.CurrentControlType
        )
        self.class_name: str = self.uia.CurrentClassName
        self.auto_id: str = self.uia.CurrentAutomationId
        self.pid: int = self.uia.CurrentProcessId
        self.rect = Rect(self.uia.CurrentBoundingRectangle)

        self.is_enabled = self.uia.CurrentIsEnabled == 1

    def set_focus(self) -> None:
        hres = self.uia.SetFocus()
        if hres < 0:
            raise ElementNotFocusedError(
                "Element was not able to be focused..."
            )
        time.sleep(0.05)

    def draw_outline(
        self,
        rect: Optional[Rect] = None,
        color: int = Color.GREEN,
        thickness: int = 2,
    ):
        if rect is None:
            rect = cast(Rect, self.rect)

        dc = win32gui.GetDC(0)

        pen = cast(int, win32gui.CreatePen(win32con.PS_SOLID, thickness, color))
        old_pen = win32gui.SelectObject(dc, pen)
        old_brush = win32gui.SelectObject(
            dc, win32gui.GetStockObject(win32con.NULL_BRUSH)
        )

        win32gui.Rectangle(dc, rect.left, rect.top, rect.right, rect.bottom)

        win32gui.SelectObject(dc, old_brush)
        win32gui.SelectObject(dc, old_pen)

        win32gui.DeleteObject(pen)
        win32gui.DeleteDC(dc)

    def __repr__(self) -> str:
        return (
            f"UIAElement(title={self.title!r}, control_type={self.control_type.name!r}, "
            f"class_name={self.class_name!r}, auto_id={self.auto_id!r}, pid={self.pid!r}, "
            f"is_enabled={self.is_enabled!r}, rect={self.rect!r})"
        )


class Condition:
    def __init__(self, hr: IUIAutomation) -> None:
        self.hr = hr
        self.repr = "Condition(<empty>)"
        self._condition = None

    @property
    def condition(self) -> IUIAutomationCondition:
        if not self._condition:
            raise ConditionNotCreatedError("Unable to create a condition...")
        return self._condition

    def create_property_condition(
        self, property_id: Property, value: Union[int, str]
    ) -> IUIAutomationCondition:
        condition = self.hr.CreatePropertyConditionEx(
            property_id, value, PropertyConditionFlags_IgnoreCase
        )
        self.repr = f"Condition({property_id=!r}, {value=!r})"
        self._condition = condition
        return self._condition

    def condition_from_array(
        self, conditions: Iterable["Condition"]
    ) -> IUIAutomationCondition:
        self._condition = self.hr.CreateAndConditionFromArray(
            [c.condition for c in conditions]
        )
        self.repr = "Condition(" + ", ".join(c.repr for c in conditions) + ")"
        return self._condition

    def __repr__(self) -> str:
        return self.repr


class Automate:
    def __init__(self) -> None:
        self.hr = comtypes.CoCreateInstance(
            CUIAutomation().IPersist_GetClassID(),
            interface=IUIAutomation,
            clsctx=comtypes.CLSCTX_INPROC_SERVER,
        )
        self.root = self.hr.GetRootElement()

    def create_condition(
        self,
        pid: Optional[int] = None,
        control_type: Optional[ControlType] = None,
        class_name: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Condition:
        if not pid and not control_type and not class_name and not title:
            raise ValueError("Every argument is None...")

        conditions: Iterable[Condition] = []

        if pid:
            sub_condition = Condition(self.hr)
            sub_condition.create_property_condition(Property.ProcessId, pid)
            conditions.append(sub_condition)

        if control_type:
            sub_condition = Condition(self.hr)
            sub_condition.create_property_condition(
                Property.ControlType, control_type
            )
            conditions.append(sub_condition)

        if class_name:
            sub_condition = Condition(self.hr)
            sub_condition.create_property_condition(
                Property.ClassName, class_name
            )
            conditions.append(sub_condition)

        if title:
            sub_condition = Condition(self.hr)
            sub_condition.create_property_condition(Property.Title, title)
            conditions.append(sub_condition)

        condition_count = len(conditions)
        if condition_count > 1:
            condition = Condition(self.hr)
            condition.condition_from_array(conditions)
        elif condition_count == 1:
            condition = conditions[0]
        else:
            raise ConditionNotCreatedError("Unable to create a condition...")

        return condition

    def find_first(self, scope: Scope, condition: Condition) -> UIAElement:
        uia = self.root.FindFirst(scope, condition.condition)
        if not uia:
            raise ElementNotFoundError(
                f"Element with condition {condition} not found..."
            )

        element = UIAElement(uia=uia)
        return element

    @staticmethod
    def iter_elements(
        elements: IUIAutomationElementArray,
    ) -> Generator[IUIAutomationElement, None, None]:
        for idx in range(elements.Length):
            element = elements.GetElement(idx)
            yield element

    def find_all(
        self, condition: Condition, scope: Scope = Scope.Children
    ) -> Iterable[UIAElement]:
        uia_array = self.root.FindAll(scope, condition.condition)
        elements = [
            UIAElement(uia=uia) for uia in self.iter_elements(uia_array)
        ]
        return elements


def main():
    auto = Automate()

    elements = auto.find_all(
        condition=auto.create_condition(
            pid=7516, control_type=ControlType.Window
        ),
    )

    for element in elements:
        print(element)


if __name__ == "__main__":
    main()
