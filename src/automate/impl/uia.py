from __future__ import annotations

import re
import time
from collections.abc import Generator, Sequence
from ctypes.wintypes import RECT
from enum import Enum
from functools import cached_property
from typing import Pattern, TypedDict, cast, override

import comtypes  # type: ignore[import-untyped]
import comtypes.client  # type: ignore[import-untyped]
from comtypes.gen import UIAutomationClient as UIAClient  # type: ignore[import-untyped]
from comtypes.gen.UIAutomationClient import (  # type: ignore[import-untyped]
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

uia_dll = comtypes.client.GetModule("UIAutomationCore.dll")


class Property(int, Enum):
    ProcessIdP = cast(int, uia_dll.UIA_ProcessIdPropertyId)
    ControlTypeP = cast(int, uia_dll.UIA_ControlTypePropertyId)
    ClassNameP = cast(int, uia_dll.UIA_ClassNamePropertyId)
    TitleP = cast(int, uia_dll.UIA_NamePropertyId)


class Scope(int, Enum):
    AncestorsS = cast(int, uia_dll.TreeScope_Ancestors)
    ChildrenS = cast(int, uia_dll.TreeScope_Children)
    DescendantsS = cast(int, uia_dll.TreeScope_Descendants)
    ElementS = cast(int, uia_dll.TreeScope_Element)
    ParentS = cast(int, uia_dll.TreeScope_Parent)
    SubtreeS = cast(int, uia_dll.TreeScope_Subtree)


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


class Condition:
    def __init__(
        self,
        ctx: UIAContext,
        native_condition: IUIAutomationCondition | None = None,
        re_pattern: Pattern[str] | None = None,
    ) -> None:
        self._ctx = ctx
        self.repr = "Condition(<empty>)"
        self._condition = native_condition
        self.re_pattern = re_pattern

    @property
    def condition(self) -> IUIAutomationCondition | None:
        return self._condition

    def __repr__(self) -> str:
        return self.repr


class TrueCondition(Condition):
    def __init__(
        self,
        ctx: UIAContext,
        native_condition: IUIAutomationCondition | None = None,
        re_pattern: Pattern[str] | None = None,
    ) -> None:
        super().__init__(ctx, native_condition, re_pattern)
        self.repr = "TrueCondition()"

    @override
    @property
    def condition(self) -> IUIAutomationCondition | None:
        return self._ctx.uia.CreateTrueCondition()

    @override
    def __repr__(self) -> str:
        return self.repr


class UIAElementInfo(TypedDict):
    title: str
    control_type: str
    class_name: str
    pid: int
    auto_id: str
    is_enabled: bool


class UIAElement(BaseElement["UIAElement"]):
    def __init__(self, ctx: UIAContext, _native: IUIAutomationElement) -> None:
        self._ctx: UIAContext = ctx
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
    def rect(self) -> Rect:
        self._rect = Rect(cast(RECT, self._native.CurrentBoundingRectangle))
        return self._rect

    @cached_property
    def control_type(self) -> ControlType:
        return ControlType(cast(str, self._native.CurrentControlType))

    @cached_property
    def class_name(self) -> str:
        return cast(str, self._native.CurrentClassName)

    @cached_property
    def auto_id(self) -> str:
        return cast(str, self._native.CurrentAutomationId)

    @cached_property
    def pid(self) -> int:
        return cast(int, self._native.CurrentProcessId)

    def get_info(self) -> UIAElementInfo:
        info = UIAElementInfo(
            title=self.title,
            control_type=self.control_type.name,
            class_name=self.class_name,
            pid=self.pid,
            auto_id=self.auto_id,
            is_enabled=self.is_enabled,
        )
        return info

    def set_focus(self, delay_after: float = 0.05) -> None:
        hres = self._native.SetFocus()
        if hres < 0:
            raise UIAElementNotFocusedError(
                "Element was not able to be focused..."
            )
        time.sleep(delay_after)

    def text(self) -> str:
        match self.control_type:
            case ControlType.Window:
                return self.title
            case ControlType.Edit:
                return self.title
                # pattern = self.uia.GetCurrentPattern(10032)
                # print(pattern.value)
                # # if not pattern:
                # #     return ""
                # iface = pattern.QueryInterface(
                #     UIAClient.IUIAutomationTextEditPattern
                # )
                # return cast(str, iface.DocumentRange.GetText(-1))
            case _:
                return self.title
        # pattern = self.uia.GetCurrentPattern(Pattern.Text.id)
        # if not pattern:
        #     return ""
        # iface = pattern.QueryInterface(Pattern.Text.iface)
        # res = cast(str, iface.DocumentRange.GetText(-1))
        # pattern = self.uia.GetCurrentPattern(Pattern.Value.id)
        # if not pattern:
        #     return ""
        # print(dir(pattern))
        # value = pattern.value
        # return value
        # return self.title

    def find_first(
        self, condition: Condition, scope: Scope = Scope.ChildrenS
    ) -> UIAElement | None:
        if condition.re_pattern:
            native_elements = self._native.FindAll(scope, condition.condition)
            for native_element in ielements(native_elements):
                title = native_element.CurrentName
                if re.match(condition.re_pattern, title):
                    return UIAElement(ctx=self._ctx, _native=native_element)
            return None
        else:
            uia = self._native.FindFirst(scope, condition.condition)

        if not uia:
            return None

        element = UIAElement(ctx=self._ctx, _native=uia)
        return element

    def find_all(
        self, condition: Condition, scope: Scope = Scope.ChildrenS
    ) -> list[UIAElement]:
        uia_array = self._native.FindAll(scope, condition.condition)
        elements = [
            UIAElement(ctx=self._ctx, _native=uia)
            for uia in ielements(uia_array)
        ]
        return elements

    def ifind_all(
        self, condition: Condition, scope: Scope = Scope.ChildrenS
    ) -> Generator[UIAElement]:
        uia_array = self._native.FindAll(scope, condition.condition)
        for uia in ielements(uia_array):
            element = UIAElement(ctx=self._ctx, _native=uia)
            yield element

    @override
    def children(self) -> list[UIAElement]:
        elements = self.find_all(condition=TrueCondition(ctx=self._ctx))
        return elements

    @override
    def ichildren(self) -> Generator[UIAElement]:
        elements = self.ifind_all(condition=TrueCondition(ctx=self._ctx))
        return elements

    @override
    def tree(
        self,
        element: UIAElement | None = None,
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

    @override
    def __repr__(self) -> str:
        return (
            f"UIAElement(title={self.title!r}, control_type={self.control_type.name!r}, "
            f"class_name={self.class_name!r}, auto_id={self.auto_id!r}, pid={self.pid!r}, "
            f"is_enabled={self.is_enabled!r}, rect={self.rect!r})"
        )


def ielements(
    elements: IUIAutomationElementArray,
) -> Generator[IUIAutomationElement]:
    for idx in range(cast(int, elements.Length)):
        element = elements.GetElement(idx)
        yield element


class UIAContext:
    def __init__(self) -> None:
        self._uia: IUIAutomation = comtypes.CoCreateInstance(
            CUIAutomation().IPersist_GetClassID(),
            interface=IUIAutomation,
            clsctx=comtypes.CLSCTX_INPROC_SERVER,
        )
        self.desktop: UIAElement = UIAElement(
            ctx=self, _native=self._uia.GetRootElement()
        )

    @property
    def uia(self) -> IUIAutomation:
        return self._uia

    def create_property_condition(
        self, property_id: Property, value: int | str
    ) -> Condition:
        native_condition = self.uia.CreatePropertyConditionEx(
            property_id, value, PropertyConditionFlags_IgnoreCase
        )
        condition = Condition(ctx=self, native_condition=native_condition)
        condition.repr = f"Condition({property_id=!r}, {value=!r})"
        return condition

    def create_true_condition(self):
        return self.uia.CreateTrueCondition()

    def condition_from_array(self, conditions: list[Condition]) -> Condition:
        re_pattern = None
        native_conditions: list[IUIAutomationCondition] = []
        for c in conditions:
            if c.condition:
                native_conditions.append(c.condition)
            if c.re_pattern:
                re_pattern = c.re_pattern

        if native_conditions:
            native_condition = self.uia.CreateAndConditionFromArray(
                native_conditions
            )
        else:
            native_condition = self.create_true_condition()

        condition = Condition(
            ctx=self, native_condition=native_condition, re_pattern=re_pattern
        )
        condition.repr = (
            "Condition(" + ", ".join(c.repr for c in conditions) + ")"
        )
        return condition

    def create_condition(
        self,
        pid: int | None = None,
        control_type: ControlType | None = None,
        class_name: str | None = None,
        title: str | Pattern[str] | None = None,
    ) -> Condition:
        if not pid and not control_type and not class_name and not title:
            raise ValueError("Every argument is None...")

        conditions: list[Condition] = []

        if pid:
            conditions.append(
                self.create_property_condition(Property.ProcessIdP, pid)
            )

        if control_type:
            conditions.append(
                self.create_property_condition(
                    Property.ControlTypeP, control_type
                )
            )

        if class_name:
            conditions.append(
                self.create_property_condition(Property.ClassNameP, class_name)
            )

        if title:
            if isinstance(title, str):
                conditions.append(
                    self.create_property_condition(Property.TitleP, title)
                )
            else:
                conditions.append(Condition(ctx=self, re_pattern=title))

        condition_count = len(conditions)
        if condition_count > 1:
            condition = self.condition_from_array(conditions)
        elif condition_count == 1:
            condition = conditions[0]
        else:
            raise UIAConditionNotCreatedError("Unable to create a condition...")

        return condition

    def windows(self) -> Sequence[UIAElement]:
        elements = self.desktop.find_all(
            condition=self.create_condition(control_type=ControlType.Window),
        )
        return elements

    def tree(
        self,
        element: UIAElement | None = None,
        max_depth: int | None = None,
        draw_outline: bool = False,
        outline_duration: float = 0.005,
    ) -> None:
        if not element:
            element = self.desktop

        element.tree(
            max_depth=max_depth,
            draw_outline=draw_outline,
            outline_duration=outline_duration,
        )
