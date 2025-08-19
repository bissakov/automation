from __future__ import annotations

import time
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, NamedTuple, cast

import comtypes.client
from comtypes import CLSCTX_INPROC_SERVER, CoCreateInstance
from typing_extensions import override

comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as UIAClient
from comtypes.gen.UIAutomationClient import (
    CUIAutomation,
    IUIAutomation,
    IUIAutomationCondition,
    IUIAutomationElement,
    IUIAutomationElementArray,
    PropertyConditionFlags_IgnoreCase,
)

from automate.common import Rect
from automate.errors import (
    UIAConditionNotCreatedError,
    UIAElementNotFocusedError,
)
from automate.impl.base import BaseElement

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from ctypes.wintypes import RECT
    from types import TracebackType
    from typing import Self

uia_dll = comtypes.client.GetModule("UIAutomationCore.dll")


class UIA:
    _instance: IUIAutomation | None = None

    @classmethod
    def instance(cls) -> IUIAutomation:
        if cls._instance is None:
            cls._instance = CoCreateInstance(
                CUIAutomation().IPersist_GetClassID(),
                interface=IUIAutomation,
                clsctx=CLSCTX_INPROC_SERVER,
            )
        return cls._instance

    @classmethod
    def release(cls) -> None:
        if cls._instance is None:
            return
        cls._instance = None


class Property(int, Enum):
    ProcessId = cast(int, uia_dll.UIA_ProcessIdPropertyId)
    ControlType = cast(int, uia_dll.UIA_ControlTypePropertyId)
    ClassName = cast(int, uia_dll.UIA_ClassNamePropertyId)
    Title = cast(int, uia_dll.UIA_NamePropertyId)


class Scope(int, Enum):
    Ancestors = cast(int, uia_dll.TreeScope_Ancestors)
    Children = cast(int, uia_dll.TreeScope_Children)
    Descendants = cast(int, uia_dll.TreeScope_Descendants)
    Element = cast(int, uia_dll.TreeScope_Element)
    Parent = cast(int, uia_dll.TreeScope_Parent)
    Subtree = cast(int, uia_dll.TreeScope_Subtree)


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


class UIAPattern(Enum):
    Annotation = (10023, UIAClient.IUIAutomationAnnotationPattern)
    CustomNavigation = (
        10033,
        UIAClient.IUIAutomationCustomNavigationPattern,
    )
    Dock = (10011, UIAClient.IUIAutomationDockPattern)
    Drag = (10030, UIAClient.IUIAutomationDragPattern)
    DropTarget = (10031, UIAClient.IUIAutomationDropTargetPattern)
    ExpandCollapse = (
        10005,
        UIAClient.IUIAutomationExpandCollapsePattern,
    )
    GridItem = (10007, UIAClient.IUIAutomationGridItemPattern)
    Grid = (10006, UIAClient.IUIAutomationGridPattern)
    Invoke = (10000, UIAClient.IUIAutomationInvokePattern)
    ItemContainer = (
        10019,
        UIAClient.IUIAutomationItemContainerPattern,
    )
    LegacyIAccessible = (
        10018,
        UIAClient.IUIAutomationLegacyIAccessiblePattern,
    )
    MultipleView = (10008, UIAClient.IUIAutomationMultipleViewPattern)
    ObjectModel = (10022, UIAClient.IUIAutomationObjectModelPattern)
    RangeValue = (10003, UIAClient.IUIAutomationRangeValuePattern)
    ScrollItem = (10017, UIAClient.IUIAutomationScrollItemPattern)
    Scroll = (10004, UIAClient.IUIAutomationScrollPattern)
    SelectionItem = (
        10010,
        UIAClient.IUIAutomationSelectionItemPattern,
    )
    Selection2 = (10034, UIAClient.IUIAutomationSelectionPattern2)
    Selection = (10001, UIAClient.IUIAutomationSelectionPattern)
    SpreadsheetItem = (
        10027,
        UIAClient.IUIAutomationSpreadsheetItemPattern,
    )
    Spreadsheet = (10026, UIAClient.IUIAutomationSpreadsheetPattern)
    Styles = (10025, UIAClient.IUIAutomationStylesPattern)
    SynchronizedInput = (
        10021,
        UIAClient.IUIAutomationSynchronizedInputPattern,
    )
    TableItem = (10013, UIAClient.IUIAutomationTableItemPattern)
    Table = (10012, UIAClient.IUIAutomationTablePattern)
    TextChild = (10029, UIAClient.IUIAutomationTextChildPattern)
    TextEdit = (10032, UIAClient.IUIAutomationTextEditPattern)
    Text2 = (10024, UIAClient.IUIAutomationTextPattern2)
    Text = (10014, UIAClient.IUIAutomationTextPattern)
    Toggle = (10015, UIAClient.IUIAutomationTogglePattern)
    Transform2 = (10028, UIAClient.IUIAutomationTransformPattern2)
    Transform = (10016, UIAClient.IUIAutomationTransformPattern)
    Value = (10002, UIAClient.IUIAutomationValuePattern)
    VirtualizedItem = (
        10020,
        UIAClient.IUIAutomationVirtualizedItemPattern,
    )
    Window = (10009, UIAClient.IUIAutomationWindowPattern)

    def __init__(self, pattern_id: int, iface: object) -> None:
        self.id = pattern_id
        self.iface = iface


def ielements(
    elements: IUIAutomationElementArray,
) -> Generator[IUIAutomationElement]:
    count = cast(int, elements.Length)
    for idx in range(count):
        element = elements.GetElement(idx)
        yield element


class Condition:
    def __init__(
        self,
        _native: IUIAutomationCondition | None = None,
        conditions: tuple[IUIAutomationCondition, ...] = (),
        reprs: tuple[str, ...] = (),
    ) -> None:
        super().__init__()

        self._native: IUIAutomationCondition | None = _native
        self.conditions: tuple[IUIAutomationCondition, ...] = conditions
        self.reprs: tuple[str, ...] = reprs

    def pid(self, pid: int) -> Condition:
        cond = self.create_property_condition(Property.ProcessId, pid)
        return Condition(
            conditions=self.conditions + (cond,),
            reprs=self.reprs + (f"({Property.ProcessId!r}, {pid!r})",),
        )

    def control_type(self, control_type: ControlType) -> Condition:
        cond = self.create_property_condition(
            Property.ControlType, control_type
        )
        return Condition(
            conditions=self.conditions + (cond,),
            reprs=self.reprs
            + (f"({Property.ControlType!r}, {control_type!r})",),
        )

    def class_name(self, class_name: str) -> Condition:
        cond = self.create_property_condition(Property.ClassName, class_name)
        return Condition(
            conditions=self.conditions + (cond,),
            reprs=self.reprs + (f"({Property.ClassName!r}, {class_name!r})",),
        )

    def title(self, title: str) -> Condition:
        cond = self.create_property_condition(Property.Title, title)
        return Condition(
            conditions=self.conditions + (cond,),
            reprs=self.reprs + (f"({Property.Title!r}, {title!r})",),
        )

    def create_property_condition(
        self, property_id: Property, value: int | str
    ) -> IUIAutomationCondition:
        native_condition = (
            UIA()
            .instance()
            .CreatePropertyConditionEx(
                property_id, value, PropertyConditionFlags_IgnoreCase
            )
        )
        return native_condition

    @property
    def native(self) -> IUIAutomationCondition | None:
        if self._native:
            return self._native

        length = len(self.conditions)
        if length == 0:
            raise UIAConditionNotCreatedError("Unable to create a condition...")

        if length > 1:
            return UIA().instance().CreateAndConditionFromArray(self.conditions)

        return self.conditions[0]

    @override
    def __repr__(self) -> str:
        return "Condition(" + ", ".join(repr for repr in self.reprs) + ")"


TRUE_CONDITION = Condition(
    _native=UIA().instance().CreateTrueCondition(),
    reprs=("True",),
)


class ElementInfo(NamedTuple):
    title: str
    control_type: str
    class_name: str
    pid: int
    auto_id: str
    is_enabled: bool


class Element(BaseElement["Element"]):
    def __init__(self, _native: IUIAutomationElement) -> None:
        super().__init__()
        self._native: IUIAutomationElement = _native
        self._title: str
        self._is_enabled: bool
        self._rect: Rect

    @property
    def title(self) -> str:
        self._title = cast(str, self._native.CurrentName)
        return self._title

    @property
    def is_enabled(self) -> bool:
        self._is_enabled = bool(cast(int, self._native.CurrentIsEnabled))
        return self._is_enabled

    @property
    @override
    def rect(self) -> Rect:
        self._rect = Rect(cast("RECT", self._native.CurrentBoundingRectangle))
        return self._rect

    @cached_property
    def control_type(self) -> ControlType:
        return ControlType(cast(int, self._native.CurrentControlType))

    @cached_property
    def class_name(self) -> str:
        return cast(str, self._native.CurrentClassName)

    @cached_property
    def auto_id(self) -> str:
        return cast(str, self._native.CurrentAutomationId)

    @cached_property
    def pid(self) -> int:
        return cast(int, self._native.CurrentProcessId)

    def get_info(self) -> ElementInfo:
        info = ElementInfo(
            title=self.title,
            control_type=self.control_type.name,
            class_name=self.class_name,
            pid=self.pid,
            auto_id=self.auto_id,
            is_enabled=self.is_enabled,
        )
        return info

    def focus(self, delay_after: float = 0.05) -> None:
        hres = self._native.SetFocus()
        if hres != 0:
            raise UIAElementNotFocusedError(
                f"{hres=!r}. Element was not able to be focused..."
            )
        time.sleep(delay_after)

    def text(self) -> str:
        match self.control_type:
            case ControlType.Window:
                return self.title
            case ControlType.Edit:
                return self.title
                # pattern = UIA().instance().GetCurrentPattern(10032)
                # print(pattern.value)
                # # if not pattern:
                # #     return ""
                # iface = pattern.QueryInterface(
                #     UIAClient.IUIAutomationTextEditPattern
                # )
                # return cast(str, iface.DocumentRange.GetText(-1))
            case _:
                return self.title
        # pattern = UIA().instance().GetCurrentPattern(Pattern.Text.id)
        # if not pattern:
        #     return ""
        # iface = pattern.QueryInterface(Pattern.Text.iface)
        # res = cast(str, iface.DocumentRange.GetText(-1))
        # pattern = UIA().instance().GetCurrentPattern(Pattern.Value.id)
        # if not pattern:
        #     return ""
        # print(dir(pattern))
        # value = pattern.value
        # return value
        # return self.title

    def find_first(
        self, condition: Condition, scope: Scope = Scope.Descendants
    ) -> Element | None:
        # if condition.re_pattern:
        #     native_elements = self._native.FindAll(scope, condition.native)
        #     for native_element in ielements(native_elements):
        #         title = native_element.CurrentName
        #         if re.match(condition.re_pattern, title):
        #             return Element(_native=native_element)
        #     return None

        uia = self._native.FindFirst(scope, condition.native)

        if not uia:
            return None

        element = Element(_native=uia)
        return element

    def find_all(
        self,
        condition: Condition,
        scope: Scope = Scope.Descendants,
    ) -> list[Element]:
        uia_array = self._native.FindAll(scope, condition.native)
        elements = [Element(_native=uia) for uia in ielements(uia_array)]
        return elements

    def ifind_all(
        self,
        condition: Condition,
        scope: Scope = Scope.Descendants,
    ) -> Generator[Element]:
        for uia in ielements(self._native.FindAll(scope, condition.native)):
            element = Element(_native=uia)
            yield element

    @override
    def children(self) -> list[Element]:
        elements = self.find_all(condition=TRUE_CONDITION, scope=Scope.Children)
        return elements

    @override
    def ichildren(self) -> Generator[Element]:
        elements = self.ifind_all(
            condition=TRUE_CONDITION, scope=Scope.Children
        )
        return elements

    @override
    def tree(
        self,
        element: Element | None = None,
        max_depth: int | None = None,
        counters: dict[str, int] | None = None,
        depth: int = 0,
        draw_outline: bool = False,
        outline_duration_ms: int = 75,
    ) -> None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be a non-negative integer or None")

        if counters is None:
            counters = {}

        if not element:
            element = self

        element_ctrl = element.control_type.name
        counters[element_ctrl] = counters.get(element_ctrl, 0) + 1
        element_idx = counters[element_ctrl] - 1

        element_repr = "▏   " * depth + f"{element_ctrl}{element_idx} - "

        if element.auto_id:
            element_repr += f"{element.auto_id!r} - "

        element_repr += f"{element.text()!r} - "

        try:
            element_repr += f"{element.rect}"
            print(element_repr)
        except Exception:
            element_repr += "(COMError)"
            print(element_repr)
            return

        if draw_outline:
            element.outline(duration_ms=outline_duration_ms)

        if max_depth is None or depth < max_depth:
            for child in element.children():
                self.tree(
                    element=child,
                    max_depth=max_depth,
                    counters=counters,
                    depth=depth + 1,
                    draw_outline=draw_outline,
                    outline_duration_ms=outline_duration_ms,
                )

    @override
    def __repr__(self) -> str:
        return (
            f"Element(title={self.title!r}, control_type={self.control_type.name!r}, "
            f"class_name={self.class_name!r}, auto_id={self.auto_id!r}, pid={self.pid!r}, "
            f"is_enabled={self.is_enabled!r}, rect={self.rect!r})"
        )


class Window(Element):
    def __init__(self, _native: IUIAutomationElement) -> None:
        super().__init__(_native)


class Context:
    @property
    def uia(self) -> IUIAutomation:
        return UIA().instance()

    @property
    def desktop(self) -> Element:
        return Element(_native=UIA().instance().GetRootElement())

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        UIA().release()

    def window(self, condition: Condition) -> Element | None:
        element = self.desktop.find_first(
            condition=condition, scope=Scope.Children
        )
        return element

    def windows(self) -> Sequence[Element]:
        elements = self.desktop.find_all(
            condition=Condition().control_type(ControlType.Window),
            scope=Scope.Children,
        )
        return elements

    def iwindows(self) -> Generator[Element]:
        return self.desktop.ifind_all(
            condition=Condition().control_type(ControlType.Window),
            scope=Scope.Children,
        )

    def find_all(
        self, condition: Condition, scope: Scope = Scope.Children
    ) -> list[Element]:
        return list(self.ifind_all(condition=condition, scope=scope))

    def ifind_all(
        self, condition: Condition, scope: Scope = Scope.Children
    ) -> Generator[Element]:
        return self.desktop.ifind_all(condition, scope)

    def tree(
        self,
        element: Element | None = None,
        max_depth: int | None = None,
        draw_outline: bool = False,
        outline_duration: int = 10,
    ) -> None:
        if not element:
            element = self.desktop

        element.tree(
            max_depth=max_depth,
            draw_outline=draw_outline,
            outline_duration_ms=outline_duration,
        )


def main() -> None:
    from time import sleep

    from automate.common import Color

    with Context() as ctx:
        for window in ctx.windows():
            print(window)

        # cond = Condition().control_type(ControlType.Window).pid(13392)
        cond = (
            Condition()
            .control_type(ControlType.Window)
            .title("Volume Mixer - Speakers (fifine Microphone)")
        )
        win = ctx.window(cond)
        if win:
            print(win)
            win.focus()
            win.click_mouse()
            btn = win.find_first(
                Condition()
                .control_type(ControlType.Button)
                .title("Mute Mozilla Firefox"),
                scope=Scope.Descendants,
            )
            print(btn)
            if btn:
                btn.click_mouse()
                sleep(1)
                btn.click_mouse()
            # # win.outline(color=Color.RED, thickness=10, duration_ms=5000)
            win.tree()


if __name__ == "__main__":
    main()
